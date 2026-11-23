"""/control → Boshqarish: Excel (.xlsx) orqali ommaviy qo'shish — faqat asosiy admin.

Yo'nalish, joy, agentlik, mehmonxona, gid va turlar uchun. Faqat matnli ma'lumotlar (nom, telefon, narx...);
rasm, logotip, sertifikat kabi fayllar Excel'ga kirmaydi — ular keyin yozuvni tahrirlashda qo'lda qo'shiladi.

Har bir qator "Yangi qo'shish" formasidan yuborilgandek `control_crud._save` orqali o'tadi — validatsiya,
slug, egasi emaili va admin tarixi bir xil ishlaydi. Fayl "hammasi yoki hech narsa": bitta qatorda xato
bo'lsa, hech qaysi qator saqlanmaydi va xatolar qator raqami bilan qaytariladi.
"""

import datetime as dt
import io
import zipfile
from types import SimpleNamespace

from django.contrib.admin.models import ADDITION
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .control_crud import (
    APPLICATION_IMPORTS,
    IMPORTABLE,
    _log,
    _res,
    _safe_field,
    _save,
    _Staff,
    application_resources,
    field_schema,
)

MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MB
MAX_ROWS = 500
SKIP_TYPES = ("image", "file")  # fayllar — faqat qo'lda

TRUE = {"ha", "yes", "true", "1", "✓", "+", "x", "bor"}
FALSE = {"yo'q", "yoq", "yo‘q", "no", "false", "0", "-", "—", "yo`q", "yo’q"}


# Modelda maydon emas, bog'liq yozuvlar: yozuv saqlangandan keyin yaratiladi (`_save_extras`)
EXTRA_COLUMNS = {
    "tour": [
        {
            "name": "_itinerary",
            "label": "Kunlik dastur",
            "type": "itinerary",
            "required": False,
            "help": "Har kun yangi qatorda (Alt+Enter) yoki «;» bilan: «Sarlavha: tavsif». 1-qator — 1-kun.",
        },
        {
            "name": "_departures",
            "label": "Jo'nash sanalari",
            "type": "departures",
            "required": False,
            "help": (
                "Vergul bilan: 2026-12-05, 2026-12-19. O'tgan sanalar tashlab yuboriladi. "
                "Joylar — «Guruhdagi maks. odam»."
            ),
        },
    ],
}


def _importable(key: str):
    if key in IMPORTABLE:
        return _res(key)
    if key in APPLICATION_IMPORTS.values():  # hamkorlik arizalari — tekshiruv navbatiga
        return application_resources()[key]
    raise NotFound("Bu bo'lim uchun Excel orqali qo'shish yo'q.")


def import_columns(res) -> list[dict]:
    """Shablon ustunlari: forma sxemasidan, fayl maydonlarisiz."""
    cols = [c for c in field_schema(res) if c["type"] not in SKIP_TYPES]
    for c in cols:
        if c["type"] == "multiselect":  # M2M (masalan, gid shaharlari) — blank=False bo'lsa majburiy
            c["required"] = not _safe_field(res, c["name"]).blank
    return cols + [dict(c) for c in EXTRA_COLUMNS.get(res.key, [])]


def _norm(s) -> str:
    return " ".join(str(s or "").replace("*", " ").split()).strip().lower()


def _header(col: dict) -> str:
    return col["label"] + (" *" if col["required"] else "")


def _format_hint(col: dict) -> str:
    t = col["type"]
    opts = col.get("options") or []
    if t == "select":
        return "Bittasi: " + ", ".join(label for _, label in opts)
    if t == "checkbox":
        return "Ha yoki Yo'q (bo'sh — Yo'q)"
    if t == "fk":
        names = ", ".join(label for _, label in opts[:15]) or "hozircha yo'q — avval qo'shing"
        return f"Nomi, slugi yoki ID. Mavjudlar: {names}" + (" …" if len(opts) > 15 else "")
    if t == "multiselect":
        names = ", ".join(label for _, label in opts[:15]) or "hozircha yo'q — avval qo'shing"
        return f"Vergul bilan bir nechta (nomi yoki ID). Mavjudlar: {names}" + (
            " …" if len(opts) > 15 else ""
        )
    if t == "tags" and opts:
        return "Vergul bilan bir nechta: " + ", ".join(label for _, label in opts)
    if t == "tags":
        return "Har bir band — yangi qatorda yoki «;» bilan"
    if t in ("itinerary", "departures"):
        return col["help"]
    if t == "number":
        return "Raqam (bo'shliqsiz yoki bo'shliq bilan: 890 000)"
    if t == "date":
        return "Sana: 2026-12-31"
    if t == "time":
        return "Vaqt: 06:00"
    if t == "email":
        return "Email"
    if t == "url":
        return "Havola: https://…"
    return "Matn"


# ---------- Shablon ----------


def build_template(res) -> bytes:
    cols = import_columns(res)
    wb = Workbook()
    ws = wb.active
    ws.title = "Ma'lumotlar"
    head_fill = PatternFill("solid", fgColor="123524")
    for i, col in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=i, value=_header(col))
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = head_fill
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = max(16, min(40, len(cell.value) + 4))
        options = None
        if col["type"] == "select":
            options = [label for _, label in col["options"]]
        elif col["type"] == "checkbox":
            options = ["Ha", "Yo'q"]
        if options:
            formula = '"' + ",".join(o.replace('"', "") for o in options) + '"'
            if len(formula) <= 255:  # Excel ro'yxat chegarasi
                dv = DataValidation(type="list", formula1=formula, allow_blank=True)
                ws.add_data_validation(dv)
                dv.add(f"{get_column_letter(i)}2:{get_column_letter(i)}{MAX_ROWS + 1}")
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "A2"

    guide = wb.create_sheet("Yo'riqnoma")
    guide.append(["Ustun", "Majburiy", "Qanday to'ldiriladi", "Izoh"])
    for c in guide[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = head_fill
    for col in cols:
        guide.append([_header(col), "Ha" if col["required"] else "", _format_hint(col), col.get("help", "")])
    guide.append([])
    guide.append(["Eslatma", "", "Ma'lumot 2-qatordan boshlanadi. Bo'sh qatorlar o'tkazib yuboriladi.", ""])
    guide.append(["", "", f"Bir faylda ko'pi bilan {MAX_ROWS} qator.", ""])
    guide.append(
        ["", "", "Rasm, logotip, sertifikat va boshqa fayllar keyin tahrirlashda qo'lda qo'shiladi.", ""]
    )
    guide.append(
        ["", "", "Bitta qatorda xato bo'lsa — hech narsa saqlanmaydi, xatolar ro'yxati chiqadi.", ""]
    )
    for letter, width in zip("ABCD", (34, 10, 70, 50), strict=True):
        guide.column_dimensions[letter].width = width
    for row in guide.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------- O'qish ----------


class CellError(Exception):
    pass


def _text(value) -> str:
    if isinstance(value, float) and value.is_integer():
        value = int(value)  # telefon, INN Excel'da raqam bo'lib qolgan bo'lsa
    if isinstance(value, dt.datetime):
        return value.isoformat()
    return str(value).strip()


def _match_option(raw: str, options: list) -> str:
    key = _norm(raw)
    for value, label in options:
        if key in (_norm(value), _norm(label)):
            return str(value)
    raise CellError("Ruxsat etilgan qiymatlardan biri bo'lsin: " + ", ".join(label for _, label in options))


def _related(res, col: dict, raw):
    """FK / M2M: ID, slug yoki nomi bo'yicha (bo'lim doirasidagi ro'yxatdan)."""
    f = _safe_field(res, col["name"])
    qs = res.fk_scope[col["name"]]() if col["name"] in res.fk_scope else f.related_model.objects.all()
    text = _text(raw)
    if text.isdigit():
        obj = qs.filter(pk=int(text)).first()
        if obj is not None:
            return obj.pk
    model_fields = {x.name for x in qs.model._meta.get_fields()}
    matches = []
    for name in ("slug", "name", "title", "display_name"):
        if name in model_fields:
            matches = list(qs.filter(**{f"{name}__iexact": text}).values_list("pk", flat=True)[:2])
            if matches:
                break
    if not matches:
        raise CellError(f"«{text}» topilmadi.")
    if len(matches) > 1:
        raise CellError(f"«{text}» bir nechta yozuvga mos keladi — ID yozing.")
    return matches[0]


def _split(text: str, *, comma: bool) -> list[str]:
    seps = ["\n", ";"] + ([","] if comma else [])
    for s in seps[1:]:
        text = text.replace(s, "\n")
    return [p.strip() for p in text.split("\n") if p.strip()]


def convert(res, col: dict, raw):
    """Excel katagi → forma qiymati. Bo'sh katak — None (maydon yuborilmaydi)."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    t = col["type"]
    if t == "select":
        return _match_option(_text(raw), col["options"])
    if t == "checkbox":
        if isinstance(raw, bool):
            return raw
        key = _norm(_text(raw))
        if key in TRUE:
            return True
        if key in FALSE:
            return False
        raise CellError("Ha yoki Yo'q yozing.")
    if t == "fk":
        return _related(res, col, raw)
    if t == "multiselect":
        return [_related(res, col, part) for part in _split(_text(raw), comma=True)]
    if t == "tags":
        opts = col.get("options")
        parts = _split(_text(raw), comma=bool(opts))
        return [_match_option(p, opts) for p in parts] if opts else parts
    if t == "number":
        if isinstance(raw, bool):
            raise CellError("Raqam kiriting.")
        if isinstance(raw, (int, float)):
            return int(raw) if float(raw).is_integer() else raw
        text = _text(raw).replace(" ", "").replace(" ", "").replace(",", ".")
        try:
            num = float(text)
        except ValueError:
            raise CellError("Raqam kiriting.") from None
        return int(num) if num.is_integer() else text
    if t == "itinerary":
        days = []
        for part in _split(_text(raw), comma=False):
            title, _, desc = part.partition(":")
            title, desc = title.strip(), desc.strip()
            if len(title) > 200:
                raise CellError(f"Kun sarlavhasi 200 belgidan oshmasin: «{title[:40]}…»")
            days.append((title, desc))
        return days
    if t == "departures":
        if isinstance(raw, (dt.datetime, dt.date)):
            parts = [raw.date() if isinstance(raw, dt.datetime) else raw]
        else:
            parts = []
            for p in _split(_text(raw), comma=True):
                try:
                    parts.append(dt.date.fromisoformat(p))
                except ValueError:
                    raise CellError(f"«{p}» — sana YYYY-MM-DD ko'rinishida bo'lsin.") from None
        # Fayl oldindan tayyorlanadi: yuklash kunigacha o'tib ketgan sanalar tashlab yuboriladi,
        # faqat hammasi o'tgan bo'lsa — xato (masalan, yil noto'g'ri yozilgan)
        today = timezone.localdate()
        upcoming = sorted({d for d in parts if d >= today})
        if parts and not upcoming:
            raise CellError("Barcha sanalar o'tib ketgan: " + ", ".join(d.isoformat() for d in parts[:5]))
        return upcoming
    if t == "date":
        if isinstance(raw, (dt.datetime, dt.date)):
            return (raw.date() if isinstance(raw, dt.datetime) else raw).isoformat()
        return _text(raw)
    if t == "time":
        if isinstance(raw, dt.datetime):
            raw = raw.time()
        if isinstance(raw, dt.time):
            return raw.strftime("%H:%M")
        return _text(raw)
    return _text(raw)


def read_rows(res, upload) -> tuple[list[tuple[int, dict]], list[dict]]:
    """Fayldan: [(qator raqami, forma ma'lumoti)] va katak xatolari. Yaroqsiz fayl — ValidationError."""
    name = (getattr(upload, "name", "") or "").lower()
    if not name.endswith(".xlsx"):
        raise ValidationError({"file": "Faqat .xlsx (Excel) fayl yuklang."})
    if upload.size > MAX_FILE_BYTES:
        raise ValidationError({"file": "Fayl 2 MB dan katta bo'lmasin."})
    try:
        wb = load_workbook(upload, read_only=True, data_only=True)
    except (zipfile.BadZipFile, KeyError, ValueError, OSError):
        raise ValidationError(
            {"file": "Faylni o'qib bo'lmadi. Shablonni yuklab olib, shuni to'ldiring."}
        ) from None
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = next(rows, None) or ()

    cols = import_columns(res)
    by_header = {}
    for col in cols:
        by_header[_norm(col["label"])] = col
        by_header[_norm(col["name"])] = col
    mapping, unknown = {}, []
    for idx, h in enumerate(header):
        if h is None or not str(h).strip():
            continue
        col = by_header.get(_norm(h))
        if col is None:
            unknown.append(str(h))
        else:
            mapping[idx] = col
    if unknown:
        raise ValidationError(
            {
                "file": "Noma'lum ustun(lar): "
                + ", ".join(unknown)
                + ". Shablondagi ustun nomlarini o'zgartirmang."
            }
        )
    missing = [_header(c) for c in cols if c["required"] and c not in mapping.values()]
    if missing:
        raise ValidationError({"file": "Majburiy ustun(lar) yo'q: " + ", ".join(missing)})

    out, errors = [], []
    for number, values in enumerate(rows, start=2):
        if not any(v is not None and str(v).strip() for v in values):
            continue
        if len(out) + len(errors) >= MAX_ROWS:
            raise ValidationError({"file": f"Bir faylda ko'pi bilan {MAX_ROWS} qator bo'lsin."})
        data, row_errors = {}, []
        for idx, col in mapping.items():
            raw = values[idx] if idx < len(values) else None
            try:
                value = convert(res, col, raw)
            except CellError as exc:
                row_errors.append(f"{col['label']}: {exc}")
                continue
            if value is not None:
                data[col["name"]] = value
        if row_errors:
            errors.append({"row": number, "errors": row_errors})
        else:
            out.append((number, data))
    wb.close()
    if not out and not errors:
        raise ValidationError({"file": "Faylda ma'lumot yo'q (2-qatordan boshlab to'ldiring)."})
    return out, errors


def _messages(detail, labels: dict) -> list[str]:
    """DRF / Django xatolarini "Maydon: xabar" ko'rinishiga keltiradi."""
    if isinstance(detail, dict):
        out = []
        for k, v in detail.items():
            label = labels.get(k, "" if k in ("detail", "non_field_errors", "__all__") else k)
            for m in _messages(v, labels):
                out.append(f"{label}: {m}" if label else m)
        return out
    if isinstance(detail, (list, tuple)):
        return [m for item in detail for m in _messages(item, labels)]
    return [str(detail)]


def run_import(res, request, upload) -> list[int]:
    labels = {c["name"]: c["label"] for c in import_columns(res)}
    rows, errors = read_rows(res, upload)
    created = []
    with transaction.atomic():
        for number, data in rows:
            extras = {
                c["name"]: data.pop(c["name"]) for c in EXTRA_COLUMNS.get(res.key, []) if c["name"] in data
            }
            fake = SimpleNamespace(data=data, user=request.user)
            try:
                with transaction.atomic():  # har bir qator — alohida savepoint
                    obj = _save(res, fake)
                    _save_extras(res, obj, extras)
            except ValidationError as exc:
                errors.append({"row": number, "errors": _messages(exc.detail, labels)})
                continue
            except DjangoValidationError as exc:
                detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
                errors.append({"row": number, "errors": _messages(detail, labels)})
                continue
            except IntegrityError:
                errors.append({"row": number, "errors": ["Takrorlanuvchi yoki noto'g'ri ma'lumot."]})
                continue
            _log(request, obj, ADDITION, f"📥 Excel'dan yaratildi ({res.title})")
            created.append(obj.pk)
        if errors:
            transaction.set_rollback(True)
    if errors:
        raise ImportFailed(sorted(errors, key=lambda e: e["row"]))
    return created


def _save_extras(res, obj, extras: dict) -> None:
    """Tur: kunlik dastur va jo'nash sanalari (joylar — guruhdagi maks. odam)."""
    if res.key != "tour":
        return
    from apps.tours.models import Departure, ItineraryDay

    days = extras.get("_itinerary") or []
    if len(days) > obj.duration_days:
        raise ValidationError(
            {
                "_itinerary": f"Dasturda {len(days)} kun, turda esa {obj.duration_days} kun"
                " — «Kunlar»ni to'g'rilang."
            }
        )
    ItineraryDay.objects.bulk_create(
        ItineraryDay(tour=obj, day_number=i, title=title, description=desc)
        for i, (title, desc) in enumerate(days, 1)
    )
    Departure.objects.bulk_create(
        Departure(tour=obj, date=d, seats_total=obj.max_group_size) for d in extras.get("_departures") or []
    )


class ImportFailed(Exception):
    def __init__(self, rows):
        self.rows = rows


# ---------- View'lar ----------


class ImportTemplateView(_Staff):
    @extend_schema(
        responses={(200, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"): bytes}
    )
    def get(self, request, res):
        r = _importable(res)
        resp = HttpResponse(
            build_template(r),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = f'attachment; filename="meyzi-{r.key}-shablon.xlsx"'
        return resp


class ImportView(_Staff):
    parser_classes = [MultiPartParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"file": {"type": "string", "format": "binary"}},
            }
        },
        responses={201: dict, 400: dict},
    )
    def post(self, request, res):
        r = _importable(res)
        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError({"file": "Excel faylni tanlang."})
        try:
            ids = run_import(r, request, upload)
        except ImportFailed as exc:
            return Response(
                {
                    "detail": f"{len(exc.rows)} ta qatorda xato — hech narsa saqlanmadi. Tuzatib, qayta yuklang.",  # noqa: E501
                    "rows": exc.rows,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"created": len(ids), "ids": ids, "detail": f"{len(ids)} ta yozuv qo'shildi."},
            status=status.HTTP_201_CREATED,
        )
