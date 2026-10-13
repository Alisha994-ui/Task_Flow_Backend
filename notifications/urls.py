from rest_framework.routers import DefaultRouter

from .views import DeviceTokenViewSet, NotificationViewSet

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")
router.register("device-tokens", DeviceTokenViewSet, basename="device-token")

urlpatterns = router.urls
