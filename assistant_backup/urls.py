from rest_framework.routers import DefaultRouter

from .views import AssistantViewSet

router = DefaultRouter()
router.register("assistant", AssistantViewSet, basename="assistant")

urlpatterns = router.urls
