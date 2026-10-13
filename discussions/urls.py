from rest_framework.routers import DefaultRouter

from .views import ProjectMessageViewSet

router = DefaultRouter()
router.register(
    "project-messages",
    ProjectMessageViewSet,
    basename="project-message",
)

urlpatterns = router.urls
