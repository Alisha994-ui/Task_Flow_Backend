from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, CommentViewSet

router = DefaultRouter()
router.register("tasks", TaskViewSet)
router.register("comments", CommentViewSet)

urlpatterns = router.urls