"""Agentlik kabineti: /api/v1/cabinet/..."""

from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.agencies.views import CabinetAgencyView
from apps.bookings.views import CabinetBookingViewSet
from apps.guides.views import (
    CabinetGuideBookingViewSet,
    CabinetGuideReviewViewSet,
    CabinetMeetingPointViewSet,
    CabinetUnavailableDateViewSet,
)
from apps.hotels.views import (
    CabinetHotelBookingViewSet,
    CabinetHotelImageViewSet,
    CabinetHotelReviewViewSet,
    CabinetRoomTypeViewSet,
)
from apps.reviews.views import CabinetReviewViewSet

from .views import CabinetDepartureViewSet, CabinetMediaViewSet, CabinetStatsView, CabinetTourViewSet

router = SimpleRouter()
router.register("tours", CabinetTourViewSet, basename="cabinet-tour")
router.register(
    r"tours/(?P<tour_slug>[-\w]+)/departures", CabinetDepartureViewSet, basename="cabinet-departure"
)
router.register(r"tours/(?P<tour_slug>[-\w]+)/media", CabinetMediaViewSet, basename="cabinet-media")
router.register("stats", CabinetStatsView, basename="cabinet-stats")
router.register("bookings", CabinetBookingViewSet, basename="cabinet-booking")
router.register("reviews", CabinetReviewViewSet, basename="cabinet-review")
# Individual gid kabineti
router.register("guide/bookings", CabinetGuideBookingViewSet, basename="cabinet-guide-booking")
router.register(
    "guide/unavailable-dates", CabinetUnavailableDateViewSet, basename="cabinet-guide-unavailable"
)
router.register("guide/meeting-points", CabinetMeetingPointViewSet, basename="cabinet-guide-meeting-point")
router.register("guide/reviews", CabinetGuideReviewViewSet, basename="cabinet-guide-review")
# Mehmonxona kabineti
router.register("hotel/rooms", CabinetRoomTypeViewSet, basename="cabinet-hotel-room")
router.register("hotel/images", CabinetHotelImageViewSet, basename="cabinet-hotel-image")
router.register("hotel/bookings", CabinetHotelBookingViewSet, basename="cabinet-hotel-booking")
router.register("hotel/reviews", CabinetHotelReviewViewSet, basename="cabinet-hotel-review")

urlpatterns = [
    path("agency/", CabinetAgencyView.as_view(), name="cabinet-agency"),
    *router.urls,
]
