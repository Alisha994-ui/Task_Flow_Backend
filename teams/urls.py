from rest_framework.routers import DefaultRouter
from .views import TeamViewSet, TeamMemberViewSet

router = DefaultRouter()
router.register("teams", TeamViewSet)
router.register("team-members", TeamMemberViewSet)

urlpatterns = router.urls