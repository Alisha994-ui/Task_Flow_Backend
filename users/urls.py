from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import AppConfigView, UserViewSet, AdminDashboardView

router = DefaultRouter()
router.register("users", UserViewSet)

urlpatterns = [
    path("admin-dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("app-config/", AppConfigView.as_view()),
]

urlpatterns += router.urls