from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AdminDashboardView

router = DefaultRouter()
router.register("users", UserViewSet)

urlpatterns = [
    path("admin-dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
]

urlpatterns += router.urls