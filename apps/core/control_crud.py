"""/control → "Boshqarish": admin yaratadigan va tahrirlaydigan ma'lumotlar (umumiy CRUD).

- Kontent (yo'nalishlar, joylar, toifalar, qo'llanmalar, savol-javob, sahifalar) — to'liq CRUD.
- Hamkorlar (agentlik, mehmonxona, gid, tur va ularning xonalari, rasmlari, sanalari) — admin yaratadi
  (`managed_by_platform=True`) va faqat shularni tahrirlaydi. Hamkorning o'zi yaratgan ma'lumotlar —
  faqat ko'rish va moderatsiya (/control/queue).
- Foydalanuvchilar — bloklash va admin qilish.

Har bir bo'lim uchun forma sxemasi model maydonlaridan avtomatik tuziladi (frontend shu sxema bo'yicha
formani chizadi). Har bir amal admin tarixiga yoziladi.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models, transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .control import _Staff

# ---------- Yordamchilar ----------


def unique_slug(model, value: str, exclude_pk=None) -> str:
    base = slugify(value)[:100] or "item"
    slug, n = base, 2
    qs = model.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    while qs.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


class FlexibleJSONField(serializers.JSONField):
    """Ro'yxat (tillar, qulayliklar, "narxga kiradi" ...): JSON yoki forma'dan JSON-satr."""

    def to_internal_value(self, data):
        if isinstance(data, (str, bytes)):
            try:
                data = json.loads(data or "[]")
            except ValueError:
                raise serializers.ValidationError("Noto'g'ri qiymat.") from None
        return super().to_internal_value(data)


def _log(request, obj, flag, message: str) -> None:
    LogEntry.objects.log_actions(
        user_id=request.user.pk, queryset=[obj], action_flag=flag, change_message=message, single_object=True
    )


def _user_by_email(email: str, *, create: bool):
    from apps.accounts.models import User

    email = (email or "").strip().lower()
    if not email:
        return None
    user = User.objects.filter(email__iexact=email).first()
    if user is None and create:
        user = User.objects.create_user(email=email)  # parolsiz — Google yoki "parolni tiklash" bilan kiradi
    return user


@dataclass
class Resource:
    key: str
    title: str
    group: str
    model: type
    fields: list[str]
    columns: list[str]
    search: list[str] = field(default_factory=list)
    can_create: bool = True
    can_delete: bool = True
    editable: Callable = field(default=lambda obj: True)
    scope: Callable | None = None  # ro'yxat (qs → qs)
    fk_scope: dict = field(default_factory=dict)  # maydon → () → queryset
    json_options: dict = field(default_factory=dict)  # JSON ro'yxat maydoni → {kod: nomi}
    extra: list = field(default_factory=list)  # modelda yo'q qo'shimcha maydonlar (masalan, egasi emaili)
    before_save: Callable | None = None  # (attrs, instance, request) → attrs
    after_save: Callable | None = None  # (obj, created, request) → None
    validate: Callable | None = None  # (attrs, instance) → attrs
    moderation_kind: str = ""  # tahrirlab bo'lmaydigan yozuv — /control/queue/<kind>/<id>
    ordering: tuple = ("-pk",)
    hint: str = ""

    def queryset(self):
        qs = self.model.objects.all()
        if self.scope:
            qs = self.scope(qs)
        return qs.order_by(*self.ordering)


def _model_field(res: Resource, name: str):
    return res.model._meta.get_field(name)


def make_serializer(res: Resource):
    attrs = {}
    extra_kwargs = {}
    for name in res.fields:
        f = _model_field(res, name)
        if isinstance(f, models.JSONField):
            attrs[name] = FlexibleJSONField(required=not f.blank and f.default is models.NOT_PROVIDED)
        elif isinstance(f, models.ForeignKey) and name in res.fk_scope:
            attrs[name] = serializers.PrimaryKeyRelatedField(
                queryset=res.fk_scope[name](), allow_null=f.null, required=not (f.null or f.blank)
            )
        elif isinstance(f, models.ManyToManyField):
            qs = res.fk_scope[name]() if name in res.fk_scope else f.related_model.objects.all()
            attrs[name] = serializers.PrimaryKeyRelatedField(
                queryset=qs, many=True, required=f.blank is False
            )
        if name == "slug":
            extra_kwargs["slug"] = {"required": False, "allow_blank": True}
    meta = type("Meta", (), {"model": res.model, "fields": ["id", *res.fields], "extra_kwargs": extra_kwargs})
    return type(f"{res.key.title()}CrudSerializer", (serializers.ModelSerializer,), {**attrs, "Meta": meta})


def _input_type(f) -> str:
    if f.choices:
        return "select"
    if isinstance(f, models.ImageField):
        return "image"
    if isinstance(f, models.FileField):
        return "file"
    if isinstance(f, models.ManyToManyField):
        return "multiselect"
    if isinstance(f, (models.ForeignKey, models.OneToOneField)):
        return "fk"
    if isinstance(f, models.JSONField):
        return "tags"
    if isinstance(f, models.BooleanField):
        return "checkbox"
    if isinstance(f, models.TextField):
        return "textarea"
    if isinstance(f, (models.IntegerField, models.DecimalField, models.FloatField)):
        return "number"
    if isinstance(f, models.DateTimeField):
        return "datetime"
    if isinstance(f, models.DateField):
        return "date"
    if isinstance(f, models.TimeField):
        return "time"
    if isinstance(f, models.EmailField):
        return "email"
    if isinstance(f, models.URLField):
        return "url"
    return "text"


def field_schema(res: Resource) -> list[dict]:
    out = []
    for name in res.fields:
        f = _model_field(res, name)
        t = _input_type(f)
        item = {
            "name": name,
            "label": str(f.verbose_name)[:1].upper() + str(f.verbose_name)[1:],
            "type": t,
            "required": not (f.blank or t == "checkbox" or f.has_default() or name == "slug"),
            "help": str(f.help_text or ""),
        }
        if name == "slug":
            item["help"] = "Bo'sh qoldirsangiz, nomidan avtomatik yasaladi."
        if t == "select":
            item["options"] = [[str(v), str(label)] for v, label in f.choices]
        elif t in ("fk", "multiselect"):
            qs = res.fk_scope[name]() if name in res.fk_scope else f.related_model.objects.all()
            item["options"] = [[str(o.pk), str(o)] for o in qs[:1000]]
            item["required"] = t == "fk" and not (f.null or f.blank)
        elif t == "tags" and name in res.json_options:
            item["options"] = [[k, v] for k, v in res.json_options[name].items()]
        out.append(item)
    for e in res.extra:
        out.append({**e, "extra": True})
    return out


def _display(obj, name: str) -> str:
    value = getattr(obj, name, "")
    if callable(value):
        value = value()
    f = None
    try:
        f = obj._meta.get_field(name)
    except Exception:  # noqa: BLE001 — model maydoni emas
        pass
    if f is not None and f.choices:
        return str(getattr(obj, f"get_{name}_display")())
    if isinstance(value, bool):
        return "✓" if value else "—"
    if value is None or value == "":
        return "—"
    return str(value)


# ---------- Bo'limlar ----------


def _set_kind(attrs, instance, file_field: str):
    """Galereya fayli: turi fayldan aniqlanadi, format/hajm va 20 rasm / 4 video chegarasi tekshiriladi."""
    from apps.core.files import check_gallery_limit, image_rule, media_kind, video_rule
    from apps.hotels.models import HotelImage
    from apps.tours.models import TourMedia

    model, parent_field = (TourMedia, "tour") if file_field == "file" else (HotelImage, "hotel")
    f = attrs.get(file_field)
    if f is not None:
        kind = media_kind(f.name) or "image"
        attrs["kind"] = kind
        (video_rule if kind == "video" else image_rule)(f)
        parent = attrs.get(parent_field) or getattr(instance, parent_field, None)
        qs = model.objects.filter(**{parent_field: parent})
        check_gallery_limit(qs, kind, exclude_pk=getattr(instance, "pk", None))
    if attrs.get("is_cover") and attrs.get("kind", getattr(instance, "kind", "image")) == "video":
        raise DjangoValidationError("Muqova faqat rasm bo'lishi mumkin.")
    return attrs


def _single_cover(obj, parent_field: str):
    if obj.is_cover:
        type(obj).objects.filter(**{parent_field: getattr(obj, parent_field)}, is_cover=True).exclude(
            pk=obj.pk
        ).update(is_cover=False)


def resources() -> dict[str, Resource]:
    from apps.accounts.models import User
    from apps.agencies.models import Agency, AgencyMember
    from apps.catalog.models import Destination, Place
    from apps.content.models import Article, FaqItem, Page
    from apps.guides.models import GuideMeetingPoint, GuideProfile, Specialization, SpokenLanguage
    from apps.hotels.models import Amenity, Hotel, HotelImage, HotelMember, RoomType
    from apps.tours.models import Departure, Tour, TourCategory, TourMedia

    def editable_agencies():
        return Agency.objects.filter(Q(is_platform=True) | Q(managed_by_platform=True))

    def managed_hotels():
        return Hotel.objects.filter(managed_by_platform=True)

    def managed_guides():
        return GuideProfile.objects.filter(managed_by_platform=True)

    def editable_tours():
        return Tour.objects.filter(Q(agency__is_platform=True) | Q(agency__managed_by_platform=True))

    owner_field = {
        "name": "owner_email",
        "label": "Egasining emaili (ixtiyoriy)",
        "type": "email",
        "required": False,
        "help": "Ko'rsatilsa — shu foydalanuvchi kabinetga kira oladi (akkaunt bo'lmasa yaratiladi).",
    }

    # --- hooklar ---
    def agency_after(obj, created, request):
        if created:
            obj.managed_by_platform = True
            obj.moderation_status = Agency.Moderation.APPROVED
            obj.save(update_fields=["managed_by_platform", "moderation_status"])
        user = _user_by_email(request.data.get("owner_email", ""), create=True)
        if user and not AgencyMember.objects.filter(user=user).exists():
            AgencyMember.objects.create(agency=obj, user=user, role=AgencyMember.Role.OWNER)
            if user.role == User.Role.TOURIST:
                user.role = User.Role.AGENCY
                user.save(update_fields=["role"])

    def hotel_after(obj, created, request):
        if created:
            obj.managed_by_platform = True
            obj.status = Hotel.Status.APPROVED
            obj.save(update_fields=["managed_by_platform", "status"])
        user = _user_by_email(request.data.get("owner_email", ""), create=True)
        if user and not HotelMember.objects.filter(user=user).exists():
            HotelMember.objects.create(hotel=obj, user=user, role=HotelMember.Role.OWNER)
            if user.role == User.Role.TOURIST:
                user.role = User.Role.BUSINESS
                user.save(update_fields=["role"])

    def guide_before(attrs, instance, request):
        if instance is None:
            user = _user_by_email(request.data.get("owner_email", ""), create=True)
            if user is None:
                raise ValidationError({"owner_email": "Gid akkaunti uchun email kiriting."})
            if GuideProfile.objects.filter(user=user).exists():
                raise ValidationError({"owner_email": "Bu foydalanuvchining gid profili allaqachon bor."})
            attrs["user"] = user
            attrs["status"] = GuideProfile.Status.APPROVED
            attrs["approved_at"] = timezone.now()
            attrs["managed_by_platform"] = True
            if user.role == User.Role.TOURIST:
                user.role = User.Role.GUIDE
                user.save(update_fields=["role"])
        return attrs

    def tour_after(obj, created, request):
        if obj.status == Tour.Status.PUBLISHED and not obj.published_at:
            obj.published_at = timezone.now()
            obj.save(update_fields=["published_at"])

    def article_before(attrs, instance, request):
        if instance is None:
            attrs["author"] = request.user
        if attrs.get("status") == Article.Status.PUBLISHED and not getattr(instance, "published_at", None):
            attrs["published_at"] = timezone.now()
        return attrs

    def no_self_demote(attrs, instance, request):
        if instance is not None and instance.pk == request.user.pk:
            if attrs.get("is_staff") is False or attrs.get("is_active") is False:
                raise ValidationError(
                    {"detail": "O'zingizni admin huquqidan yoki faollikdan chiqara olmaysiz."}
                )
        return attrs

    lang = dict(SpokenLanguage.choices)
    spec = dict(Specialization.choices)
    amen = dict(Amenity.choices)
    K, H, U = "Kontent", "Hamkorlar (platforma boshqaradi)", "Foydalanuvchilar"

    items = [
        # ---------- Kontent ----------
        Resource(
            "destination",
            "Yo'nalishlar (shaharlar)",
            K,
            Destination,
            [
                "name",
                "slug",
                "region",
                "short_description",
                "description",
                "cover_image",
                "latitude",
                "longitude",
                "is_featured",
                "is_published",
                "sort_order",
            ],
            ["name", "region", "is_featured", "is_published"],
            ["name", "region"],
            ordering=("sort_order", "name"),
        ),
        Resource(
            "place",
            "Diqqatga sazovor joylar",
            K,
            Place,
            [
                "destination",
                "name",
                "slug",
                "category",
                "short_description",
                "description",
                "history",
                "address",
                "latitude",
                "longitude",
                "opening_hours",
                "entry_fee_uzs",
                "visit_duration_minutes",
                "cover_image",
                "audio_guide",
                "is_featured",
                "is_published",
            ],
            ["name", "destination", "category", "is_published"],
            ["name", "address"],
            ordering=("name",),
        ),
        Resource(
            "tour_category",
            "Tur toifalari",
            K,
            TourCategory,
            ["name", "slug", "icon", "sort_order", "is_active"],
            ["name", "icon", "is_active"],
            ["name"],
            ordering=("sort_order", "name"),
        ),
        Resource(
            "article",
            "Qo'llanmalar (maqolalar)",
            K,
            Article,
            ["title", "slug", "excerpt", "body", "cover", "destination", "status", "tours"],
            ["title", "status", "published_at"],
            ["title", "excerpt"],
            before_save=article_before,
        ),
        Resource(
            "faq",
            "Savol-javob",
            K,
            FaqItem,
            ["question", "answer", "sort_order", "is_active"],
            ["question", "is_active"],
            ["question", "answer"],
            ordering=("sort_order", "pk"),
        ),
        Resource(
            "page",
            "Sahifalar (shartlar, maxfiylik...)",
            K,
            Page,
            ["slug", "title", "body", "is_published"],
            ["title", "slug", "is_published"],
            ["title", "slug"],
            ordering=("slug",),
        ),
        # ---------- Hamkorlar ----------
        Resource(
            "agency",
            "Agentliklar",
            H,
            Agency,
            [
                "name",
                "slug",
                "logo",
                "description",
                "phone",
                "email",
                "telegram",
                "website",
                "address",
                "inn",
                "license_number",
                "commission_percent",
                "is_verified",
            ],
            ["name", "phone", "status", "moderation_status", "managed_by_platform"],
            ["name", "phone", "inn"],
            editable=lambda o: o.is_platform or o.managed_by_platform,
            extra=[owner_field],
            after_save=agency_after,
            moderation_kind="agency",
            can_delete=False,
            hint="Siz yaratgan agentliklarni tahrirlaysiz. Hamkorlar o'zi yaratganlari — faqat moderatsiya.",
        ),
        Resource(
            "hotel",
            "Mehmonxonalar",
            H,
            Hotel,
            [
                "name",
                "slug",
                "kind",
                "destination",
                "stars",
                "description",
                "address",
                "latitude",
                "longitude",
                "phone",
                "email",
                "amenities",
                "check_in_time",
                "check_out_time",
                "cancellation_policy",
                "commission_percent",
                "is_featured",
            ],
            ["name", "destination", "status", "managed_by_platform"],
            ["name", "address", "phone"],
            editable=lambda o: o.managed_by_platform,
            json_options={"amenities": amen},
            extra=[owner_field],
            after_save=hotel_after,
            moderation_kind="hotel",
            can_delete=False,
            hint="Yaratilgach: xona turlari va rasmlarni quyidagi bo'limlarda qo'shing.",
        ),
        Resource(
            "room_type",
            "Mehmonxona xonalari",
            H,
            RoomType,
            [
                "hotel",
                "name",
                "description",
                "capacity",
                "beds",
                "size_m2",
                "price_per_night_uzs",
                "total_rooms",
                "amenities",
                "image",
                "is_active",
            ],
            ["name", "hotel", "price_per_night_uzs", "is_active"],
            ["name", "hotel__name"],
            scope=lambda qs: qs.filter(hotel__managed_by_platform=True),
            fk_scope={"hotel": managed_hotels},
            json_options={"amenities": amen},
        ),
        Resource(
            "hotel_media",
            "Mehmonxona rasm va videolari",
            H,
            HotelImage,
            ["hotel", "image", "caption", "is_cover", "sort_order"],
            ["hotel", "kind", "is_cover"],
            ["hotel__name"],
            scope=lambda qs: qs.filter(hotel__managed_by_platform=True),
            fk_scope={"hotel": managed_hotels},
            validate=lambda attrs, inst: _set_kind(attrs, inst, "image"),
            after_save=lambda obj, created, request: _single_cover(obj, "hotel"),
            hint="Rasm — jpg/png/webp, 6 MB gacha (20 ta); video — mp4/mov/webm, 20 MB gacha (4 ta).",
        ),
        Resource(
            "guide",
            "Gidlar",
            H,
            GuideProfile,
            [
                "display_name",
                "slug",
                "photo",
                "bio",
                "phone",
                "languages",
                "specializations",
                "destinations",
                "experience_years",
                "certificate_number",
                "certificate_file",
                "is_certified",
                "price_half_day_uzs",
                "price_full_day_uzs",
                "price_per_day_uzs",
                "group_surcharge_percent",
                "max_group_size",
                "commission_percent",
            ],
            ["display_name", "phone", "status", "managed_by_platform"],
            ["display_name", "phone"],
            editable=lambda o: o.managed_by_platform,
            json_options={"languages": lang, "specializations": spec},
            extra=[
                {
                    **owner_field,
                    "label": "Gid akkauntining emaili",
                    "required": True,
                    "help": "Gid shu email bilan kiradi (akkaunt bo'lmasa yaratiladi). Faqat yaratishda.",
                }
            ],
            before_save=guide_before,
            moderation_kind="guide",
            can_delete=False,
        ),
        Resource(
            "meeting_point",
            "Gid uchrashuv joylari",
            H,
            GuideMeetingPoint,
            ["guide", "destination", "name", "address", "latitude", "longitude", "is_active"],
            ["name", "guide", "destination", "is_active"],
            ["name", "address"],
            scope=lambda qs: qs.filter(guide__managed_by_platform=True),
            fk_scope={"guide": managed_guides},
        ),
        Resource(
            "tour",
            "Turlar",
            H,
            Tour,
            [
                "agency",
                "destination",
                "title",
                "slug",
                "short_description",
                "description",
                "categories",
                "places",
                "duration_days",
                "duration_nights",
                "max_group_size",
                "departure_time",
                "return_time",
                "meeting_point",
                "meeting_latitude",
                "meeting_longitude",
                "meeting_map_url",
                "price_uzs",
                "price_note",
                "cancellation_policy",
                "included",
                "not_included",
                "what_to_bring",
                "status",
                "is_featured",
            ],
            ["title", "agency", "price_uzs", "status"],
            ["title", "agency__name"],
            editable=lambda o: o.agency.is_platform or o.agency.managed_by_platform,
            fk_scope={"agency": editable_agencies},
            after_save=tour_after,
            moderation_kind="tour",
            hint="Platforma yoki siz yaratgan agentlik turlari. Rasm va sanalar — quyidagi bo'limlarda.",
        ),
        Resource(
            "tour_media",
            "Tur rasm va videolari",
            H,
            TourMedia,
            ["tour", "file", "caption", "is_cover", "sort_order"],
            ["tour", "kind", "is_cover"],
            ["tour__title"],
            scope=lambda qs: qs.filter(
                Q(tour__agency__is_platform=True) | Q(tour__agency__managed_by_platform=True)
            ),
            fk_scope={"tour": editable_tours},
            validate=lambda attrs, inst: _set_kind(attrs, inst, "file"),
            after_save=lambda obj, created, request: _single_cover(obj, "tour"),
            hint="Rasm — jpg/png/webp, 6 MB gacha (20 ta); video — mp4/mov/webm, 20 MB gacha (4 ta).",
        ),
        Resource(
            "departure",
            "Jo'nash sanalari",
            H,
            Departure,
            ["tour", "date", "seats_total", "price_uzs", "status"],
            ["tour", "date", "seats_total", "seats_booked", "status"],
            ["tour__title"],
            scope=lambda qs: qs.filter(
                Q(tour__agency__is_platform=True) | Q(tour__agency__managed_by_platform=True)
            ),
            fk_scope={"tour": editable_tours},
            ordering=("-date",),
        ),
        # ---------- Foydalanuvchilar ----------
        Resource(
            "user",
            "Foydalanuvchilar",
            U,
            User,
            ["first_name", "last_name", "role", "is_active", "is_staff"],
            ["email", "phone", "first_name", "role", "is_active", "is_staff"],
            ["email", "phone", "first_name", "last_name"],
            can_create=False,
            can_delete=False,
            before_save=no_self_demote,
            ordering=("-date_joined",),
            hint="Bloklash yoki admin qilish. Email va telefonni foydalanuvchining o'zi o'zgartiradi.",
        ),
    ]
    return {r.key: r for r in items}


def _res(key: str) -> Resource:
    r = resources().get(key)
    if r is None:
        raise NotFound("Bunday bo'lim yo'q.")
    return r


def _row(res: Resource, obj) -> dict:
    editable = res.editable(obj)
    return {
        "id": obj.pk,
        "cells": [_display(obj, c) for c in res.columns],
        "editable": editable,
        "moderation_url": f"/control/queue/{res.moderation_kind}/{obj.pk}"
        if not editable and res.moderation_kind
        else "",
    }


def _meta(res: Resource) -> dict:
    return {
        "key": res.key,
        "title": res.title,
        "group": res.group,
        "can_create": res.can_create,
        "can_delete": res.can_delete,
        "hint": res.hint,
        "columns": [
            str(_model_field(res, c).verbose_name)
            if c in {f.name for f in res.model._meta.get_fields()}
            else c
            for c in res.columns
        ],
    }


def _save(res: Resource, request, instance=None):
    ser_class = make_serializer(res)
    ser = ser_class(instance, data=request.data, partial=instance is not None, context={"request": request})
    ser.is_valid(raise_exception=True)
    attrs = dict(ser.validated_data)
    try:
        if res.validate:
            attrs = res.validate(attrs, instance)
    except DjangoValidationError as exc:
        raise ValidationError({"detail": list(exc.messages)}) from None
    if res.before_save:
        attrs = res.before_save(attrs, instance, request)
    name_field = next((n for n in ("name", "title", "display_name") if n in res.fields), None)
    if "slug" in res.fields and not attrs.get("slug") and (instance is None or "slug" in attrs):
        source = attrs.get(name_field) if name_field else None
        source = source or (getattr(instance, name_field, "") if instance and name_field else "")
        attrs["slug"] = getattr(instance, "slug", "") or unique_slug(res.model, source or res.key)
    m2m = {k: attrs.pop(k) for k in list(attrs) if isinstance(_safe_field(res, k), models.ManyToManyField)}
    with transaction.atomic():
        if instance is None:
            obj = res.model(**attrs)
        else:
            obj = instance
            for k, v in attrs.items():
                setattr(obj, k, v)
        try:
            obj.full_clean(validate_unique=False)
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
            ) from None
        obj.save()
        for k, v in m2m.items():
            getattr(obj, k).set(v)
        if res.after_save:
            res.after_save(obj, instance is None, request)
    return obj


def _safe_field(res, name):
    try:
        return res.model._meta.get_field(name)
    except Exception:  # noqa: BLE001
        return None


class CrudIndexView(_Staff):
    @extend_schema(responses={200: dict})
    def get(self, request):
        return Response([{**_meta(r), "count": r.queryset().count()} for r in resources().values()])


class CrudListView(_Staff):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @extend_schema(responses={200: dict})
    def get(self, request, res):
        r = _res(res)
        qs = r.queryset()
        q = (request.query_params.get("q") or "").strip()
        if q and r.search:
            cond = Q()
            for s in r.search:
                cond |= Q(**{f"{s}__icontains": q})
            qs = qs.filter(cond)
        total = qs.count()
        page = max(int(request.query_params.get("page") or 1), 1)
        size = 50
        rows = [_row(r, o) for o in qs[(page - 1) * size : page * size]]
        return Response(
            {
                **_meta(r),
                "schema": field_schema(r),
                "results": rows,
                "count": total,
                "page": page,
                "pages": (total + size - 1) // size,
            }
        )

    @extend_schema(request=None, responses={201: dict})
    def post(self, request, res):
        r = _res(res)
        if not r.can_create:
            raise PermissionDenied("Bu bo'limda yangi yozuv qo'shilmaydi.")
        obj = _save(r, request)
        _log(request, obj, ADDITION, f"➕ Yaratildi ({r.title})")
        return Response({"id": obj.pk}, status=status.HTTP_201_CREATED)


class CrudDetailView(_Staff):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _obj(self, r):
        return get_object_or_404(r.queryset(), pk=self.kwargs["pk"])

    @extend_schema(responses={200: dict})
    def get(self, request, res, pk):
        r = _res(res)
        obj = self._obj(r)
        data = make_serializer(r)(obj, context={"request": request}).data
        return Response(
            {
                **_meta(r),
                "schema": field_schema(r),
                "id": obj.pk,
                "name": str(obj),
                "editable": r.editable(obj),
                "data": data,
            }
        )

    @extend_schema(request=None, responses={200: dict})
    def patch(self, request, res, pk):
        r = _res(res)
        obj = self._obj(r)
        if not r.editable(obj):
            raise PermissionDenied(
                "Bu ma'lumotni hamkorning o'zi kiritgan — admin o'zgartira olmaydi (faqat moderatsiya)."
            )
        obj = _save(r, request, obj)
        _log(request, obj, CHANGE, f"✏️ Tahrirlandi ({r.title})")
        return Response({"id": obj.pk})

    @extend_schema(responses={204: None})
    def delete(self, request, res, pk):
        r = _res(res)
        obj = self._obj(r)
        if not r.can_delete or not r.editable(obj):
            raise PermissionDenied("Bu yozuvni o'chirib bo'lmaydi.")
        _log(request, obj, DELETION, f"🗑 O'chirildi ({r.title})")
        try:
            obj.delete()
        except ProtectedError:
            raise ValidationError(
                {"detail": "Bog'langan ma'lumotlar bor (masalan, bronlar) — o'chirib bo'lmaydi."}
            ) from None
        return Response(status=status.HTTP_204_NO_CONTENT)
