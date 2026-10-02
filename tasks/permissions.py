from rest_framework.permissions import BasePermission


class TaskPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role in [
            "ADMIN",
            "PROJECT_MANAGER",
            "TEAM_LEAD",
        ]:
            return True

        if request.user.role == "EMPLOYEE":
            return request.method in ["GET", "PATCH"]

        if request.user.role == "VIEWER":
            return request.method == "GET"

        return False

    def has_object_permission(self, request, view, obj):
        role = request.user.role

        if role == "ADMIN":
            return True

        if role == "PROJECT_MANAGER":
            return obj.project.manager == request.user

        if role == "TEAM_LEAD":
            return obj.project.team and obj.project.team.team_lead == request.user

        if role == "EMPLOYEE":
            if request.method == "GET":
                return (
                    obj.assignee == request.user
                    or obj.creator == request.user
                )

            if request.method == "PATCH":
                return obj.assignee == request.user

        if role == "VIEWER":
            return request.method == "GET"

        return False

class CommentPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "ADMIN":
            return True

        if request.user.role in ["PROJECT_MANAGER", "TEAM_LEAD", "EMPLOYEE"]:
            return request.method in ["GET", "POST", "PATCH"]

        if request.user.role == "VIEWER":
            return request.method == "GET"

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True

        task = obj.task

        if request.user.role == "PROJECT_MANAGER":
            return task.project.manager == request.user

        if request.user.role == "TEAM_LEAD":
            return (
                task.project.team
                and task.project.team.team_lead == request.user
            )

        if request.user.role == "EMPLOYEE":
            return task.assignee == request.user

        if request.user.role == "VIEWER":
            return request.method == "GET"

        return False

class AttachmentPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "ADMIN":
            return True

        if request.user.role in [
            "PROJECT_MANAGER",
            "TEAM_LEAD",
            "EMPLOYEE",
        ]:
            return request.method in ["GET", "POST"]

        if request.user.role == "VIEWER":
            return request.method == "GET"

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True

        task = obj.task

        if request.user.role == "PROJECT_MANAGER":
            return task.project.manager == request.user

        if request.user.role == "TEAM_LEAD":
            return (
                task.project.team
                and task.project.team.team_lead == request.user
            )

        if request.user.role == "EMPLOYEE":
            return task.assignee == request.user

        if request.user.role == "VIEWER":
            return request.method == "GET"

        return False

class TimeLogPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "ADMIN":
            return True

        if request.user.role in [
            "PROJECT_MANAGER",
            "TEAM_LEAD",
            "EMPLOYEE",
        ]:
            return request.method in ["GET", "POST"]

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True

        return obj.user == request.user

class ActivityLogPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "ADMIN":
            return True

        return request.method == "GET"

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True

        return request.method == "GET"\

class SubtaskPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "ADMIN":
            return True

        if request.user.role in [
            "PROJECT_MANAGER",
            "TEAM_LEAD",
            "EMPLOYEE",
        ]:
            return request.method in ["GET", "POST", "PATCH"]

        if request.user.role == "VIEWER":
            return request.method == "GET"

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True

        task = obj.task

        if request.user.role == "PROJECT_MANAGER":
            return task.project.manager == request.user

        if request.user.role == "TEAM_LEAD":
            return (
                task.project.team
                and task.project.team.team_lead == request.user
            )

        if request.user.role == "EMPLOYEE":
            return task.assignee == request.user

        if request.user.role == "VIEWER":
            return request.method == "GET"

        return False


class LabelPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "ADMIN":
            return True

        if request.user.role in [
            "PROJECT_MANAGER",
            "TEAM_LEAD",
        ]:
            return request.method in ["GET", "POST", "PATCH", "DELETE"]

        return request.method == "GET"

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True

        if request.user.role in ["PROJECT_MANAGER", "TEAM_LEAD"]:
            return True

        return request.method == "GET"