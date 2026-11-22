---
name: meyzi-new-app
description: MEYZI loyihasiga yangi Django ilova (app) yoki yangi model/endpoint qo'shish tartibi — gidlar, mehmonxonalar, bronlar, to'lovlar va h.k. Yangi bosqichni boshlashda, model, serializer, viewset, URL, admin yoki test yozishda ishlating.
---

# MEYZI: yangi ilova / endpoint qo'shish

Loyiha: `/mnt/d/meyzi` (Windows: `D:\meyzi`). Django 5.2 + DRF. Foydalanuvchi bilan **o'zbek tilida** gaplashing.
Kod izohlari, `verbose_name`, xato xabarlari ham o'zbekcha (lotin).

## 1. Ilova yaratish

```
apps/<nom>/
  __init__.py
  apps.py            class <Nom>Config(AppConfig): name = "apps.<nom>"; verbose_name = "..."
  models.py
  serializers.py
  views.py
  urls.py
  admin.py
  filters.py         (kerak bo'lsa)
  services.py        (biznes mantiq ko'p bo'lsa — bron, to'lov)
  migrations/__init__.py
```

So'ng:
- `config/settings/base.py` → `LOCAL_APPS` ga `"apps.<nom>"` qo'shing.
- `config/urls.py` → `api_v1` ro'yxatiga `path("<nom>/", include("apps.<nom>.urls"))`.

## 2. Modellar — qoidalar

- Hamma model `apps.core.models.TimeStampedModel` dan meros oladi (`created_at`, `updated_at`).
- Foydalanuvchiga havola: `settings.AUTH_USER_MODEL` (to'g'ridan `User` import qilmang).
- Har bir maydonga o'zbekcha `verbose_name` (birinchi argument), `Meta` da `verbose_name`, `verbose_name_plural`, `ordering`.
- Tanlovlar: `models.TextChoices` (`"qiymat", "O'zbekcha nom"`).
- Pul: **`DecimalField(max_digits=12, decimal_places=2)`** + alohida `currency` maydoni (`UZS`/`USD`).
  Hech qachon `FloatField` emas. So'mdagi butun narx uchun `PositiveIntegerField` mumkin (katalogdagi `entry_fee_uzs` kabi).
- Ommaviy obyektlar uchun `slug` (unique) va `is_published`; API'da `lookup_field = "slug"`.
- Ko'p filtrlanadigan maydonlarga `Meta.indexes`.
- O'chirishda: bog'liq biznes ma'lumot uchun `on_delete=models.PROTECT`, faqat bola obyektlar (rasm va h.k.) uchun `CASCADE`.

## 3. Serializer va view

- Ro'yxat va batafsil uchun alohida serializer (`XListSerializer`, `XDetailSerializer(XListSerializer)`), yozish uchun `XWriteSerializer`.
  `get_serializer_class()` da `self.action` bo'yicha tanlang.
- `get_queryset()` da `select_related` / `prefetch_related` — N+1 bo'lmasin.
- Annotatsiya (`Count`, `Sum`) bo'lsa, oxirida aniq `.order_by(...)` qo'ying (aks holda pagination ogohlantirishi).
- Ruxsatlar: `apps.core.permissions.IsAdminOrReadOnly` (katalog turidagi ma'lumot), egasi uchun alohida permission yozing
  (`IsOwner`, `IsGuide` va h.k. — `apps/core/permissions.py` ga).
- Rol tekshiruvi: `request.user.role == User.Role.GUIDE`. Admin — `is_staff`.
- Filtrlar: `filterset_class` (`filters.py`), `search_fields`, `ordering_fields`.
- Murakkab mantiq (narx hisoblash, holat o'zgarishi, pul) — **view ichida emas**, `services.py` dagi funksiyada,
  `transaction.atomic` bilan. View faqat chaqiradi.
- Swagger: oddiy `APIView` da `@extend_schema(request=..., responses=...)`; serializer `@property` larga type hint (`-> bool`).
- Router: `SimpleRouter` (bitta `include` ichida bir nechta ilova bo'lsa `DefaultRouter` ning ildiz sahifasi to'qnashadi).
  Bo'sh prefiks (`register("", ...)`) ishlatilsa, aniq prefikslarni undan **oldin** ro'yxatdan o'tkazing.
- Ichma-ich resurslar: `router.register(r"tours/(?P<tour_slug>[-\w]+)/departures", ...)` va
  `apps/tours/views.py` dagi `_TourChildMixin` kabi ota obyektni egasi bo'yicha tekshiradigan mixin.
- Swagger: `get_queryset`/`get_serializer_class` `request.user` yoki `request.agency` ga bog'liq bo'lsa, boshida
  `if getattr(self, "swagger_fake_view", False): return Model.objects.none()`. Yangi `status` enum bo'lsa —
  `SPECTACULAR_SETTINGS["ENUM_NAME_OVERRIDES"]` ga qo'shing. Tekshirish: `manage.py spectacular --file /dev/null`
  ogohlantirishsiz bo'lsin.

## 3a. Agentlik kabineti

- Ruxsat: `apps.agencies.permissions.IsAgencyMember` — faol agentlik xodimini tekshiradi va `request.agency` ni o'rnatadi.
- Kabinet URL'lari `apps/tours/cabinet_urls.py` da (`/api/v1/cabinet/...`). Yangi kabinet resursini shu yerga qo'shing.
- Queryset doim `agency=self.request.agency` bilan cheklanadi; begona obyekt — `404` (403 emas).
- Agentlik o'zgartira olmaydigan maydonlar (`status`, `commission_percent`, `is_verified`, `rating`...) — `read_only_fields`.
- Slug server tomonda: `apps.agencies.services.unique_slug(Model, nom)`.

## 4. Admin

`@admin.register`, `list_display`, `list_filter`, `search_fields`, slug uchun `prepopulated_fields`, FK uchun `autocomplete_fields`
(bog'langan admin'da `search_fields` bo'lishi shart), bola modellar `TabularInline`.

## 5. Testlar

- Fayl: `tests/test_<nom>.py`, boshida `pytestmark = pytest.mark.django_db`.
- Umumiy fixture'lar `tests/conftest.py` da: `api` (anonim), `user`, `auth_api`, `admin_user`, `admin_api`, `samarqand`, `registon`,
  `agency`, `agency_user`, `agency_api` (kabinet), `category`, `tour` (e'lon qilingan), `departure` (7 kundan keyin, 20 joy), `PASSWORD`.
  Fayl yuklash testlarida `settings.MEDIA_ROOT = tmp_path` (`tests/test_tours.py` dagi `media_tmp`).
  Har bir autentifikatsiyali fixture **o'z `APIClient()`** ini yaratadi — bitta client'ni bo'lishmang.
- Yangi umumiy obyektlar (gid, mehmonxona) uchun fixture'ni `conftest.py` ga qo'shing.
- Har bir endpoint uchun kamida: muvaffaqiyatli holat, ruxsat yo'q (401/403), validatsiya xatosi (400), yashirin obyekt (404).
- Biznes qoidalar (bekor qilish foizlari, komissiya) — `services` funksiyalarini to'g'ridan-to'g'ri test qiling, chegaraviy qiymatlar bilan.

## 6. Yakunlash

1. `python manage.py makemigrations <nom>` (test sozlamalari bilan — `meyzi-verify` skill'iga qarang).
2. `meyzi-verify` skill'idagi tekshiruvlarni bajaring.
3. `README.md` ni yangilang: API jadvali, filtrlar, yo'l xaritasidagi belgi `[x]`.
4. Foydalanuvchi so'ramaguncha commit qilmang.
