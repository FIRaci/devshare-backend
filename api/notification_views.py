from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from notifications.models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the notifications
        for the currently authenticated user.
        """
        return self.request.user.notifications.all().order_by('-timestamp')

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Mark all unread notifications for the user as read.
        """
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
