from django.db import router
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, SubtaskViewSet, CommentViewSet, LabelViewSet, AttachmentViewSet, ActivityLogViewSet, TimeLogViewSet, TimeLogViewSet
router = DefaultRouter()
router.register("tasks", TaskViewSet)
router.register("subtasks", SubtaskViewSet)
router.register("comments", CommentViewSet)
router.register("labels", LabelViewSet)
router.register("attachments", AttachmentViewSet)
router.register("activity-logs", ActivityLogViewSet)
router.register("time-logs", TimeLogViewSet)

urlpatterns = router.urls