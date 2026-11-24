"""/control → Boshqarish: Excel orqali rasm havolalari (gid surati, agentlik logotipi, mehmonxona galereyasi).

Shablonda mavjud yozuvlar nomi bilan oldindan to'ldiriladi — admin faqat havolalarni qo'yadi. Server har bir
havolani o'zi yuklab oladi, haqiqiy rasm/video ekanini tekshiradi va saqlaydi (Cloudinary yoqilgan bo'lsa —
o'sha yerga). Tashqi saytdagi rasmga to'g'ridan-to'g'ri bog'lanmaymiz: u o'chsa, bizda ham yo'qolardi.

Qatorlar bir-biriga bog'liq emas: bitta havola ishlamasa, qolganlari saqlanadi; natija har bir havola uchun
qaytariladi. Faqat hamkor/platforma yozuvlari biriktiriladi — `media_import.attach` bilan bir xil qoidalar
(format, hajm, galereya chegarasi, bir faylni ikki marta biriktirmaslik).
"""

import io
import ipaddress
import socket
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, urlparse

from django.contrib.admin.models import CHANGE
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from .control_crud import _log, _res, _Staff
from .files import IMAGE_MAX_MB, MB, VIDEO_MAX_MB, sniff_image, sniff_video
from .media_import import Skip, attach, resolve

MAX_LINKS = 300
MAX_FILE_BYTES = 2 * MB  # Excel faylning o'zi
TIMEOUT = 15  # bitta havola, soniya
WORKERS = 8
_IMAGE_EXT = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}

# bo'lim → (sarlavha, nom ustuni, [(ustun nomi, "image" | "video"), ...])
SECTIONS = {
    "guide": ("Gidlar", "Ism", [("Rasm havolasi", "image")]),
    "agency": ("Agentliklar", "Nomi", [("Logotip havolasi", "image")]),
    "hotel": (
        "Mehmonxonalar",
        "Nomi",
        [(f"Rasm {i}", "image") for i in range(1, 9)] + [(f"Video {i}", "video") for i in range(1, 3)],
    ),
}


def _section(key: str):
    if key not in SECTIONS:
        raise NotFound("Bu bo'lim uchun rasm havolalari yo'q.")
    return SECTIONS[key]


def _records(key: str):
    from .media_import import _models

    model, name_field = _models()[key]
    return model.objects.order_by(name_field).values_list("slug", name_field)


# ---------- Shablon ----------


def build_template(key: str) -> bytes:
    title, name_col, link_cols = _section(key)
    wb = Workbook()
    ws = wb.active
    ws.title = "Havolalar"
    ws.append([f"{name_col} *", "Slug", *[c for c, _ in link_cols]])
    head = PatternFill("solid", fgColor="1F5F4A")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = head
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    for slug, name in _records(key):
        ws.append([name, slug])
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 26
    for i in range(len(link_cols)):
        ws.column_dimensions[chr(ord("C") + i)].width = 48
    ws.freeze_panes = "C2"

    info = wb.create_sheet("Yo'riqnoma")
    for row in [
        ["Nima qilish kerak"],
        [f"{title}: har bir qatorga rasm havolasini qo'ying. Nom va slug ustunlarini o'zgartirmang."],
        ["Havola to'g'ridan-to'g'ri faylga olib borsin (brauzerda ochilganda faqat rasm ko'rinsin)."],
        ["Instagram/Facebook sahifasi, Google qidiruv natijasi, YouTube havolasi — ishlamaydi."],
        [f"Rasm: jpg, png yoki webp, {IMAGE_MAX_MB} MB gacha."],
        [f"Video: mp4, mov yoki webm, {VIDEO_MAX_MB} MB gacha."],
        ["Bo'sh katak — o'tkazib yuboriladi. Gid surati va logotip yangisi bilan almashtiriladi;"],
        ["mehmonxonaga rasmlar galereyaga qo'shiladi (birinchi rasm muqova bo'ladi, agar muqova bo'lmasa)."],
        ["Faqat o'zingizga tegishli yoki foydalanishga ruxsat olingan rasmlarni qo'ying."],
    ]:
        info.append(row)
    info.column_dimensions["A"].width = 110
    info["A1"].font = Font(bold=True)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------- Havoladan yuklab olish ----------


def _check_host(url: str) -> None:
    """Faqat http(s) va ochiq internet manzillari (server ichki tarmog'iga so'rov yuborilmaydi)."""
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise Skip("Havola http:// yoki https:// bilan boshlansin.")
    try:
        infos = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == "https" else 80))
    except (socket.gaierror, UnicodeError):
        raise Skip("Sayt topilmadi — havolani tekshiring.") from None
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise Skip("Bu manzilga ruxsat yo'q.")


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _check_host(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_SafeRedirect)


# Qidiruv tizimlarining "rasm sahifasi" havolalari: asl rasm manzili parametrda turadi
_WRAPPERS = (
    ("google.", ("imgurl", "url", "q")),
    ("yandex.", ("img_url",)),
    ("bing.com", ("mediaurl",)),
)
MAX_SOURCE_MB = 25  # katta rasm yuklab olinadi va kichraytiriladi
MAX_SIDE = 2560


def unwrap(url: str) -> str:
    """Bo'shliqlarni olib tashlaydi; Google/Yandex/Bing rasm havolasidan asl manzilni oladi."""
    url = "".join((url or "").split())
    p = urlparse(url)
    host = (p.hostname or "").lower()
    params = parse_qs(p.query)
    for marker, keys in _WRAPPERS:
        if marker in host:
            for k in keys:
                inner = (params.get(k) or [""])[0]
                if inner.startswith(("http://", "https://")):
                    return inner
    return url


def _shrink(data: bytes) -> tuple[str, bytes]:
    """Katta rasm → eng uzun tomoni 2560 px, JPEG (6 MB chegarasiga sig'adi)."""
    from PIL import Image, ImageOps

    with Image.open(io.BytesIO(data)) as img:
        img = ImageOps.exif_transpose(img)
        img.thumbnail((MAX_SIDE, MAX_SIDE))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        for quality in (85, 75, 65):
            out = io.BytesIO()
            img.save(out, "JPEG", quality=quality, optimize=True)
            if out.tell() <= IMAGE_MAX_MB * MB:
                return "jpg", out.getvalue()
    raise Skip(f"Rasm juda katta ({IMAGE_MAX_MB} MB gacha kichraytirib bo'lmadi).")


def download(url: str, kind: str) -> tuple[str, bytes]:
    """`kind`: "image" | "video" | "auto". → (kengaytma, baytlar). Muammo bo'lsa — Skip (sababi bilan)."""
    url = unwrap(url)
    _check_host(url)
    limit = (VIDEO_MAX_MB if kind == "video" else max(MAX_SOURCE_MB, VIDEO_MAX_MB)) * MB
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (MEYZI media import)"})
    try:
        with _opener.open(req, timeout=TIMEOUT) as resp:  # noqa: S310 — sxema va manzil tekshirilgan
            data = resp.read(limit + 1)
    except urllib.error.HTTPError as exc:
        raise Skip(f"Sayt xato qaytardi ({exc.code}).") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise Skip("Havolani ochib bo'lmadi (sayt javob bermadi).") from None
    if len(data) > limit:
        raise Skip(f"Fayl juda katta ({limit // MB} MB dan oshmasin).")
    f = io.BytesIO(data)
    if kind in ("image", "auto"):
        fmt = sniff_image(f)
        if fmt in _IMAGE_EXT:
            if len(data) > IMAGE_MAX_MB * MB:
                return _shrink(data)
            return _IMAGE_EXT[fmt], data
        if kind == "image":
            raise Skip(
                "Havola rasm emas (sahifa yoki noma'lum format). To'g'ridan-to'g'ri rasm havolasi kerak."
            )
    ext = sniff_video(f)
    if ext is None:
        if kind == "auto":
            raise Skip("Havola rasm yoki video emas (sahifa). To'g'ridan-to'g'ri fayl havolasi kerak.")
        raise Skip("Havola video fayl emas (mp4, mov yoki webm kerak; YouTube havolasi ishlamaydi).")
    if len(data) > VIDEO_MAX_MB * MB:
        raise Skip(f"Video juda katta ({VIDEO_MAX_MB} MB dan oshmasin).")
    return ext, data


# ---------- Bitta yozuvga havolalar (tahrirlash sahifasidan) ----------

LINKABLE = ("tour", "hotel", "guide", "agency")  # media_import.attach bo'limlari bilan bir xil
MAX_RECORD_LINKS = 20


def add_links(key: str, obj, urls: list[str]) -> list[dict]:
    urls = [u for u in ("".join(x.split()) for x in urls) if u][:MAX_RECORD_LINKS]

    def fetch(url):
        try:
            return download(url, "auto"), None
        except Skip as exc:
            return None, str(exc)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        fetched = list(pool.map(fetch, urls))
    out = []
    base = (getattr(obj, "slug", "") or "fayl")[:60]
    for url, (got, err) in zip(urls, fetched, strict=True):
        item = {"url": url, "ok": False, "message": err or ""}
        if got:
            try:
                item["message"] = attach(key, obj, f"{base}.{got[0]}", got[1])
                item["ok"] = True
            except Skip as exc:
                item["message"] = str(exc)
        out.append(item)
    return out


# ---------- Excel'ni o'qish va biriktirish ----------


def read_links(key: str, upload) -> list[dict]:
    _, name_col, link_cols = _section(key)
    if upload.size > MAX_FILE_BYTES:
        raise ValidationError({"file": "Excel fayl 2 MB dan oshmasin."})
    try:
        wb = load_workbook(upload, read_only=True, data_only=True)
    except Exception:  # noqa: BLE001 — buzilgan / .xlsx emas
        raise ValidationError({"file": "Faylni o'qib bo'lmadi — .xlsx formatida yuklang."}) from None
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = [str(c or "").strip().rstrip("*").strip().lower() for c in next(rows, [])]
    try:
        i_name = header.index(name_col.lower())
    except ValueError:
        raise ValidationError({"file": f"«{name_col}» ustuni topilmadi — shablonni yuklab oling."}) from None
    i_slug = header.index("slug") if "slug" in header else None
    cols = [(header.index(c.lower()), c, kind) for c, kind in link_cols if c.lower() in header]
    if not cols:
        raise ValidationError({"file": "Havola ustunlari topilmadi — shablonni yuklab oling."})

    def cell(row, i) -> str:
        return str(row[i]).strip() if i is not None and i < len(row) and row[i] is not None else ""

    out = []
    for n, row in enumerate(rows, start=2):
        links = [(c, kind, cell(row, i)) for i, c, kind in cols if cell(row, i)]
        if links:
            name = cell(row, i_name)
            out.append({"row": n, "key": cell(row, i_slug) or name, "name": name, "links": links})
    if sum(len(r["links"]) for r in out) > MAX_LINKS:
        raise ValidationError({"file": f"Bir faylda ko'pi bilan {MAX_LINKS} ta havola."})
    return out


def run(key: str, request, upload) -> dict:
    rows = read_links(key, upload)
    jobs = [(r, col, kind, url) for r in rows for col, kind, url in r["links"]]

    def fetch(job):
        _, _, kind, url = job
        try:
            return download(url, kind), None
        except Skip as exc:
            return None, str(exc)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        fetched = list(pool.map(fetch, jobs))

    cache, results, done, touched = {}, [], 0, {}
    for (r, col, _kind, url), (got, err) in zip(jobs, fetched, strict=True):
        item = {"row": r["row"], "name": r["name"], "column": col, "url": url, "ok": False, "message": ""}
        try:
            obj = resolve(key, r["key"], cache)
            if err:
                raise Skip(err)
            ext, data = got
            base = (getattr(obj, "slug", "") or "fayl")[:60]
            item["message"] = attach(key, obj, f"{base}.{ext}", data)
            item["ok"] = True
            done += 1
            touched[obj.pk] = obj
        except Skip as exc:
            item["message"] = str(exc)
        results.append(item)
    for obj in touched.values():
        _log(request, obj, CHANGE, "🖼 Rasm havolalari (Excel) orqali yangilandi")
    failed = len(results) - done
    return {
        "done": done,
        "failed": failed,
        "results": results,
        "detail": f"{done} ta fayl saqlandi" + (f", {failed} tasi o'tmadi." if failed else "."),
    }


class PhotoLinksTemplateView(_Staff):
    @extend_schema(
        responses={(200, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"): bytes}
    )
    def get(self, request, res):
        resp = HttpResponse(
            build_template(res),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = f'attachment; filename="meyzi-{res}-rasm-havolalari.xlsx"'
        return resp


class PhotoLinksView(_Staff):
    parser_classes = [MultiPartParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"file": {"type": "string", "format": "binary"}},
            }
        },
        responses={200: dict},
    )
    def post(self, request, res):
        _section(res)
        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError({"file": "Excel faylni tanlang."})
        return Response(run(res, request, upload))


class RecordLinksView(_Staff):
    """Tahrirlash sahifasidan: bitta yozuvga havola(lar) orqali rasm/video."""

    parser_classes = [JSONParser]

    @extend_schema(request={"application/json": {"type": "object"}}, responses={200: dict})
    def post(self, request, res, pk):
        if res not in LINKABLE:
            raise NotFound("Bu bo'limga havola orqali rasm qo'shilmaydi.")
        obj = get_object_or_404(_res(res).queryset(), pk=pk)
        raw = request.data.get("urls") or []
        urls = raw.splitlines() if isinstance(raw, str) else [str(u) for u in raw]
        urls = [u for u in urls if u.strip()]
        if not urls:
            raise ValidationError({"urls": "Havolani kiriting."})
        results = add_links(res, obj, urls)
        done = sum(r["ok"] for r in results)
        if done:
            _log(request, obj, CHANGE, f"🖼 Havola orqali {done} ta fayl qo'shildi")
        failed = len(results) - done
        return Response(
            {
                "done": done,
                "results": results,
                "detail": f"{done} ta fayl qo'shildi" + (f", {failed} tasi o'tmadi." if failed else "."),
            }
        )
