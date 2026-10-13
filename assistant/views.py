from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AssistantMessage
from .serializers import AssistantMessageSerializer
from .services import AssistantError, ask


class AssistantViewSet(viewsets.GenericViewSet):
    """The in-app assistant.

    GET  /api/assistant/          the thread
    POST /api/assistant/ask/      ask something
    POST /api/assistant/clear/    start over
    """

    serializer_class = AssistantMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # A thread belongs to one person and nobody else.
        return AssistantMessage.objects.filter(user=self.request.user)

    def list(self, request):
        messages = self.get_queryset().order_by("created_at")

        return Response(
            AssistantMessageSerializer(messages, many=True).data
        )

    @action(detail=False, methods=["post"], url_path="ask")
    def ask(self, request):
        question = (request.data.get("question") or "").strip()

        if not question:
            return Response({"detail": "Ask something first."}, status=400)

        if len(question) > 2000:
            return Response(
                {"detail": "That question is too long."},
                status=400,
            )

        try:
            answer = ask(request.user, question)
        except AssistantError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"answer": answer})

    @action(detail=False, methods=["post"], url_path="clear")
    def clear(self, request):
        self.get_queryset().delete()

        return Response({"message": "Conversation cleared."})
