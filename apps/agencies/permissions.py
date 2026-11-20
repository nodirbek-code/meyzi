from rest_framework.permissions import BasePermission

from .services import get_user_agency


class IsAgencyMember(BasePermission):
    """Faqat faol agentlik xodimlari. View'da agentlik `request.agency` orqali olinadi."""

    message = "Bu bo'lim faqat faol turagentlik xodimlari uchun."

    def has_permission(self, request, view):
        agency = get_user_agency(request.user)
        request.agency = agency
        return agency is not None
