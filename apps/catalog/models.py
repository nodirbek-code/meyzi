from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel

LAT_VALIDATORS = [MinValueValidator(-90), MaxValueValidator(90)]
LNG_VALIDATORS = [MinValueValidator(-180), MaxValueValidator(180)]


class Destination(TimeStampedModel):
    """Shahar yoki hudud: Samarqand, Buxoro, Xiva..."""

    name = models.CharField("nomi", max_length=120)
    slug = models.SlugField("slug", max_length=140, unique=True)
    region = models.CharField("viloyat", max_length=120, blank=True)
    short_description = models.CharField("qisqa tavsif", max_length=300, blank=True)
    description = models.TextField("tavsif", blank=True)
    cover_image = models.ImageField("muqova rasmi", upload_to="destinations/", blank=True)
    latitude = models.DecimalField(
        "kenglik", max_digits=9, decimal_places=6, null=True, blank=True, validators=LAT_VALIDATORS
    )
    longitude = models.DecimalField(
        "uzunlik", max_digits=9, decimal_places=6, null=True, blank=True, validators=LNG_VALIDATORS
    )
    is_featured = models.BooleanField("tavsiya etiladi", default=False)
    is_published = models.BooleanField("e'lon qilingan", default=True)
    sort_order = models.PositiveIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "shahar / hudud"
        verbose_name_plural = "shaharlar / hududlar"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class PlaceCategory(models.TextChoices):
    MONUMENT = "monument", "Tarixiy obida"
    MOSQUE = "mosque", "Masjid / madrasa"
    MUSEUM = "museum", "Muzey"
    BAZAAR = "bazaar", "Bozor"
    NATURE = "nature", "Tabiat"
    CRAFT = "craft", "Hunarmandchilik"
    RESTAURANT = "restaurant", "Restoran / milliy taom"
    PARK = "park", "Park"
    OTHER = "other", "Boshqa"


class Place(TimeStampedModel):
    """Diqqatga sazovor joy: Registon, Ark qal'asi, Ichan Qal'a..."""

    destination = models.ForeignKey(
        Destination, on_delete=models.PROTECT, related_name="places", verbose_name="shahar"
    )
    name = models.CharField("nomi", max_length=200)
    slug = models.SlugField("slug", max_length=220, unique=True)
    category = models.CharField(
        "toifa", max_length=20, choices=PlaceCategory.choices, default=PlaceCategory.MONUMENT
    )
    short_description = models.CharField("qisqa tavsif", max_length=300, blank=True)
    description = models.TextField("tavsif", blank=True)
    history = models.TextField("tarixi", blank=True)
    address = models.CharField("manzil", max_length=255, blank=True)
    latitude = models.DecimalField(
        "kenglik", max_digits=9, decimal_places=6, null=True, blank=True, validators=LAT_VALIDATORS
    )
    longitude = models.DecimalField(
        "uzunlik", max_digits=9, decimal_places=6, null=True, blank=True, validators=LNG_VALIDATORS
    )
    opening_hours = models.CharField(
        "ish vaqti", max_length=120, blank=True, help_text="Masalan: 08:00–19:00"
    )
    entry_fee_uzs = models.PositiveIntegerField("kirish narxi (so'm)", default=0)
    visit_duration_minutes = models.PositiveIntegerField(
        "tavsiya etilgan tashrif davomiyligi (daqiqa)", default=60
    )
    cover_image = models.ImageField("muqova rasmi", upload_to="places/", blank=True)
    audio_guide = models.FileField("audio-gid", upload_to="audio/", blank=True)
    is_featured = models.BooleanField("tavsiya etiladi", default=False)
    is_published = models.BooleanField("e'lon qilingan", default=True)

    class Meta:
        verbose_name = "joy"
        verbose_name_plural = "joylar"
        ordering = ["destination__sort_order", "name"]
        indexes = [models.Index(fields=["destination", "category"])]

    def __str__(self):
        return f"{self.name} ({self.destination})"

    @property
    def is_free(self) -> bool:
        return self.entry_fee_uzs == 0


class PlaceImage(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("rasm", upload_to="places/gallery/")
    caption = models.CharField("izoh", max_length=200, blank=True)
    sort_order = models.PositiveIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "rasm"
        verbose_name_plural = "rasmlar"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.caption or f"{self.place} rasmi"
