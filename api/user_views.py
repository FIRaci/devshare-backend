from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action  # Thêm import này
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, ProfileSerializer, MyTokenObtainPairSerializer
from users.models import Profile, UserFollowing

User = get_user_model()

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, username=None):
        user_to_follow = self.get_object()
        user_from = request.user
        if user_to_follow == user_from:
            return Response({'error': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        UserFollowing.objects.get_or_create(user_from=user_from, user_to=user_to_follow)
        return Response({'status': 'following'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unfollow(self, request, username=None):
        user_to_unfollow = self.get_object()
        user_from = request.user
        UserFollowing.objects.filter(user_from=user_from, user_to=user_to_unfollow).delete()
        return Response({'status': 'unfollowed'})