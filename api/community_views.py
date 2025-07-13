from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from communities.models import Community

class MuteCommunityToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, community_id):
        profile = request.user.profile
        try:
            community = Community.objects.get(pk=community_id)
            if profile.muted_communities.filter(pk=community_id).exists():
                profile.muted_communities.remove(community)
                return Response({'status': 'unmuted'})
            else:
                profile.muted_communities.add(community)
                return Response({'status': 'muted'})
        except Community.DoesNotExist:
            return Response({'error': 'Community not found'}, status=status.HTTP_404_NOT_FOUND)