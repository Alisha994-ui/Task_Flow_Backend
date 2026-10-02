from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet,
    ProjectMemberViewSet,
    MilestoneViewSet,
)

router = DefaultRouter()
router.register("projects", ProjectViewSet)
router.register("project-members", ProjectMemberViewSet)
router.register("milestones", MilestoneViewSet)

urlpatterns = router.urls