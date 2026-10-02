from rest_framework.permissions import BasePermission


class ProjectPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        role = request.user.role

        if role == "ADMIN":
            return True

        if role == "PROJECT_MANAGER":
            return request.method in ["GET", "POST", "PATCH", "PUT"]

        if role == "TEAM_LEAD":
            return request.method == "GET"

        if role in ["EMPLOYEE", "VIEWER"]:
            return request.method == "GET"

        return False

    def has_object_permission(self, request, view, obj):
        role = request.user.role

        if role == "ADMIN":
            return True

        if role == "PROJECT_MANAGER":
            return obj.manager == request.user

        if role == "TEAM_LEAD":
            return obj.team and obj.team.team_lead == request.user

        if role in ["EMPLOYEE", "VIEWER"]:
            return request.method == "GET"

        return False
    
class ProjectMemberPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "ADMIN":
            return True

        if request.user.role == "PROJECT_MANAGER":
            return request.method in ["GET", "POST", "DELETE"]

        return request.method == "GET"

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True

        if request.user.role == "PROJECT_MANAGER":
            return obj.project.manager == request.user

        return request.method == "GET"


class MilestonePermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "ADMIN":
            return True

        if request.user.role == "PROJECT_MANAGER":
            return request.method in ["GET", "POST", "PATCH", "PUT", "DELETE"]

        return request.method == "GET"

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True

        if request.user.role == "PROJECT_MANAGER":
            return obj.project.manager == request.user

        if request.user.role == "TEAM_LEAD":
            return (
                obj.project.team
                and obj.project.team.team_lead == request.user
                and request.method in ["GET", "PATCH", "PUT"]
            )

        return request.method == "GET"