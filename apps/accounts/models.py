from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email majburiy")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.Role.ADMIN)
        if not extra["is_staff"] or not extra["is_superuser"]:
            raise ValueError("Superuser is_staff=True va is_superuser=True bo'lishi kerak")
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Platforma foydalanuvchisi. Login — email orqali."""

    class Role(models.TextChoices):
        TOURIST = "tourist", "Turist"
        GUIDE = "guide", "Gid"
        AGENCY = "agency", "Turagentlik xodimi"
        BUSINESS = "business", "Biznes (mehmonxona va h.k.)"
        ADMIN = "admin", "Administrator"

    class Language(models.TextChoices):
        """Platforma tillari (boshlanishiga 3 ta). Yangi til — settings.LANGUAGES bilan birga qo'shiladi."""

        UZ = "uz", "O'zbekcha"
        RU = "ru", "Русский"
        EN = "en", "English"

    email = models.EmailField("email", unique=True)
    first_name = models.CharField("ism", max_length=100, blank=True)
    last_name = models.CharField("familiya", max_length=100, blank=True)
    phone = models.CharField("telefon", max_length=20, blank=True)
    role = models.CharField("rol", max_length=20, choices=Role.choices, default=Role.TOURIST)
    language = models.CharField("til", max_length=5, choices=Language.choices, default=Language.UZ)
    country = models.CharField("mamlakat", max_length=2, blank=True, help_text="ISO kod: UZ, US, CN...")
    avatar = models.ImageField("avatar", upload_to="avatars/", blank=True)

    is_active = models.BooleanField("faol", default=True)
    is_staff = models.BooleanField("admin panelga kirish", default=False)
    date_joined = models.DateTimeField("ro'yxatdan o'tgan", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "foydalanuvchi"
        verbose_name_plural = "foydalanuvchilar"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
