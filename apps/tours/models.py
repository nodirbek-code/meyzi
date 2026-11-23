from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.catalog.models import LAT_VALIDATORS, LNG_VALIDATORS
from apps.core.files import media_rule
from apps.core.models import TimeStampedModel


class TourCategory(TimeStampedModel):
    """Tur toifasi: Tog', Madaniy, Sarguzasht, Dam olish kuni... Admin paneldan qo'shiladi."""

    name = models.CharField("nomi", max_length=100)
    slug = models.SlugField("slug", max_length=120, unique=True)
    icon = models.CharField("ikonka", max_length=50, blank=True, help_text="Emoji yoki ikonka nomi")
    sort_order = models.PositiveIntegerField("tartib", default=0)
    is_active = models.BooleanField("faol", default=True)

    class Meta:
        verbose_name = "tur toifasi"
        verbose_name_plural = "tur toifalari"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class CancellationPolicy(models.TextChoices):
    """Bekor qilish siyosati. Aniq qoidalar — apps/tours/policies.py."""

    FREE = "free", "Bepul bekor qilish"
    PARTIAL = "partial", "Qisman qaytarish"
    NON_REFUNDABLE = "non_refundable", "Qaytarilmaydi"


class Tour(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Qoralama"
        PENDING_REVIEW = "pending_review", "Moderatsiyada"
        PUBLISHED = "published", "E'lon qilingan"
        REJECTED = "rejected", "Rad etilgan"
        ARCHIVED = "archived", "Arxivda"

    agency = models.ForeignKey(
        "agencies.Agency", on_delete=models.PROTECT, related_name="tours", verbose_name="agentlik"
    )
    destination = models.ForeignKey(
        "catalog.Destination", on_delete=models.PROTECT, related_name="tours", verbose_name="yo'nalish"
    )
    categories = models.ManyToManyField(TourCategory, related_name="tours", verbose_name="toifalar")
    places = models.ManyToManyField(
        "catalog.Place", related_name="tours", blank=True, verbose_name="tashrif buyuriladigan joylar"
    )
    # Tur jamoasi: kim olib boradi va qayerda tunaladi (ommaga faqat tasdiqlanganlari ko'rinadi)
    guides = models.ManyToManyField(
        "guides.GuideProfile", related_name="tours", blank=True, verbose_name="gidlar"
    )
    hotels = models.ManyToManyField(
        "hotels.Hotel", related_name="tours", blank=True, verbose_name="mehmonxonalar"
    )

    title = models.CharField("nomi", max_length=200)
    slug = models.SlugField("slug", max_length=220, unique=True)
    short_description = models.CharField("qisqa tavsif", max_length=300, blank=True)
    description = models.TextField("tavsif", blank=True)

    duration_days = models.PositiveSmallIntegerField(
        "kunlar", default=1, validators=[MinValueValidator(1), MaxValueValidator(60)]
    )
    duration_nights = models.PositiveSmallIntegerField("kechalar", default=0)
    max_group_size = models.PositiveSmallIntegerField("guruhdagi maks. odam", default=20)
    departure_time = models.TimeField("jo'nash vaqti", null=True, blank=True)
    return_time = models.TimeField("qaytish vaqti", null=True, blank=True)

    meeting_point = models.CharField("uchrashuv joyi", max_length=255)
    meeting_latitude = models.DecimalField(
        "uchrashuv kengligi", max_digits=9, decimal_places=6, null=True, blank=True, validators=LAT_VALIDATORS
    )
    meeting_longitude = models.DecimalField(
        "uchrashuv uzunligi", max_digits=9, decimal_places=6, null=True, blank=True, validators=LNG_VALIDATORS
    )
    meeting_map_url = models.URLField("xarita havolasi", blank=True)

    price_uzs = models.PositiveIntegerField("narx (so'm, 1 kishi)")
    # Har bir turda sayohat yo'lboshchisi bor (narxga kiradi). Professional gid — ixtiyoriy qo'shimcha:
    # turist bron qilganda turga biriktirilgan gidlardan birini tanlaydi, narx guruh uchun bir marta.
    # Bo'sh — qo'shimcha gid xizmati yo'q (biriktirilgan gid bo'lsa, u narxga kiradi).
    guide_price_uzs = models.PositiveIntegerField(
        "gid xizmati narxi (so'm, guruh uchun)",
        null=True,
        blank=True,
        help_text="Ixtiyoriy professional gid — guruh uchun bir marta. Bo'sh — gid narxga kiradi yoki yo'q.",
    )
    price_note = models.CharField(
        "narx izohi", max_length=200, blank=True, help_text="Masalan: 2 kishilik xonada 1 kishi uchun"
    )
    cancellation_policy = models.CharField(
        "bekor qilish siyosati",
        max_length=20,
        choices=CancellationPolicy.choices,
        default=CancellationPolicy.FREE,
    )
    included = models.JSONField("narxga kiradi", default=list, blank=True)
    not_included = models.JSONField("narxga kirmaydi", default=list, blank=True)
    what_to_bring = models.JSONField("o'zingiz bilan oling", default=list, blank=True)

    status = models.CharField("holat", max_length=20, choices=Status.choices, default=Status.DRAFT)
    moderation_note = models.TextField("moderator izohi", blank=True)
    published_at = models.DateTimeField("e'lon qilingan vaqt", null=True, blank=True)
    is_featured = models.BooleanField("mashhur / tavsiya", default=False)

    rating = models.DecimalField("reyting", max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField("sharhlar soni", default=0)

    class Meta:
        verbose_name = "tur"
        verbose_name_plural = "turlar"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "destination"]),
            models.Index(fields=["price_uzs"]),
        ]

    def __str__(self):
        return self.title

    def publish(self):
        self.status = self.Status.PUBLISHED
        if not self.published_at:
            self.published_at = timezone.now()


class TourMedia(models.Model):
    class Kind(models.TextChoices):
        IMAGE = "image", "Rasm"
        VIDEO = "video", "Video"

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="media")
    kind = models.CharField("turi", max_length=10, choices=Kind.choices, default=Kind.IMAGE)
    file = models.FileField("fayl", upload_to="tours/", validators=[media_rule])
    caption = models.CharField("izoh", max_length=200, blank=True)
    is_cover = models.BooleanField("muqova", default=False)
    sort_order = models.PositiveIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "media"
        verbose_name_plural = "media"
        ordering = ["-is_cover", "sort_order", "id"]

    def __str__(self):
        return f"{self.tour} — {self.get_kind_display()}"


class ItineraryDay(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="itinerary")
    day_number = models.PositiveSmallIntegerField("kun", validators=[MinValueValidator(1)])
    title = models.CharField("sarlavha", max_length=200, blank=True)
    description = models.TextField("tavsif", blank=True)

    class Meta:
        verbose_name = "dastur kuni"
        verbose_name_plural = "dastur kunlari"
        ordering = ["day_number"]
        constraints = [models.UniqueConstraint(fields=["tour", "day_number"], name="uniq_tour_day")]

    def __str__(self):
        return f"{self.tour} — {self.day_number}-kun"


class ItineraryItem(models.Model):
    day = models.ForeignKey(ItineraryDay, on_delete=models.CASCADE, related_name="items")
    start_time = models.TimeField("boshlanish", null=True, blank=True)
    end_time = models.TimeField("tugash", null=True, blank=True)
    title = models.CharField("nima bo'ladi", max_length=255)
    description = models.TextField("batafsil", blank=True)
    is_extra_cost = models.BooleanField("o'z hisobidan", default=False)
    sort_order = models.PositiveIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "dastur bandi"
        verbose_name_plural = "dastur bandlari"
        ordering = ["sort_order", "start_time", "id"]

    def __str__(self):
        return self.title


class Departure(TimeStampedModel):
    """Turning aniq jo'nash sanasi va joylar soni."""

    class Status(models.TextChoices):
        OPEN = "open", "Sotuvda"
        CLOSED = "closed", "Sotuv yopilgan"
        CANCELLED = "cancelled", "Bekor qilingan"

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="departures")
    date = models.DateField("sana")
    seats_total = models.PositiveSmallIntegerField("jami joylar")
    seats_booked = models.PositiveSmallIntegerField("band qilingan joylar", default=0)
    price_uzs = models.PositiveIntegerField(
        "maxsus narx (so'm)", null=True, blank=True, help_text="Bo'sh bo'lsa — tur narxi"
    )
    status = models.CharField("holat", max_length=20, choices=Status.choices, default=Status.OPEN)

    class Meta:
        verbose_name = "jo'nash sanasi"
        verbose_name_plural = "jo'nash sanalari"
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(fields=["tour", "date"], name="uniq_tour_departure_date"),
            models.CheckConstraint(
                condition=models.Q(seats_booked__lte=models.F("seats_total")), name="seats_booked_lte_total"
            ),
        ]

    def __str__(self):
        return f"{self.tour} — {self.date}"

    @property
    def seats_left(self) -> int:
        return max(self.seats_total - self.seats_booked, 0)

    @property
    def effective_price(self) -> int:
        return self.price_uzs if self.price_uzs is not None else self.tour.price_uzs

    @property
    def is_bookable(self) -> bool:
        if self.status != self.Status.OPEN or self.seats_left <= 0:
            return False
        today = timezone.localdate()
        if self.date != today:
            return self.date > today
        # bugun: jo'nash vaqti o'tgan bo'lsa — bron qilib bo'lmaydi (vaqt yo'q bo'lsa kun boshi — o'tgan)
        start = self.tour.departure_time
        return bool(start) and timezone.localtime().time() < start
