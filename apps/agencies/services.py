from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.notifications import user_events

from .models import Agency, AgencyApplication, AgencyMember


def unique_slug(model, value, field="slug"):
    base = slugify(value) or "item"
    slug, n = base, 2
    while model.objects.filter(**{field: slug}).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


@transaction.atomic
def approve_application(application: AgencyApplication, reviewer: User) -> Agency:
    """Arizani tasdiqlaydi: agentlik yaratiladi, ariza bergan foydalanuvchi uning egasi bo'ladi."""
    application = AgencyApplication.objects.select_for_update().get(pk=application.pk)
    if application.status in (AgencyApplication.Status.APPROVED, AgencyApplication.Status.REJECTED):
        raise ValidationError({"detail": "Ariza allaqachon ko'rib chiqilgan."})

    owner = application.user
    if owner and AgencyMember.objects.filter(user=owner).exists():
        raise ValidationError({"detail": "Bu foydalanuvchi allaqachon boshqa agentlik xodimi."})

    agency = Agency.objects.create(
        name=application.agency_name,
        slug=unique_slug(Agency, application.agency_name),
        phone=application.phone,
        email=application.email,
        is_verified=True,
    )
    if owner:
        AgencyMember.objects.create(agency=agency, user=owner, role=AgencyMember.Role.OWNER)
        if owner.role == User.Role.TOURIST:
            owner.role = User.Role.AGENCY
            owner.save(update_fields=["role"])

    application.status = AgencyApplication.Status.APPROVED
    application.agency = agency
    application.reviewed_by = reviewer
    application.reviewed_at = timezone.now()
    application.save()
    user_events.agency_application_reviewed(application)
    return agency


@transaction.atomic
def reject_application(application: AgencyApplication, reviewer: User, note: str = "") -> AgencyApplication:
    application = AgencyApplication.objects.select_for_update().get(pk=application.pk)
    if application.status in (AgencyApplication.Status.APPROVED, AgencyApplication.Status.REJECTED):
        raise ValidationError({"detail": "Ariza allaqachon ko'rib chiqilgan."})
    application.status = AgencyApplication.Status.REJECTED
    application.admin_note = note
    application.reviewed_by = reviewer
    application.reviewed_at = timezone.now()
    application.save()
    user_events.agency_application_reviewed(application)
    return application


def get_user_agency(user) -> Agency | None:
    """Foydalanuvchi a'zo bo'lgan faol agentlik (yoki None)."""
    if not user or not user.is_authenticated:
        return None
    membership = AgencyMember.objects.select_related("agency").filter(user=user).first()
    if membership and membership.agency.is_active:
        return membership.agency
    return None
