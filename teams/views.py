from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Team, TeamMember
from .serializers import TeamSerializer, TeamMemberSerializer

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all().order_by("-created_at")
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.all().order_by("-joined_at")
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated]