from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views
from .views import (
    PostViewSet, TagViewSet, CommentViewSet, CommunityViewSet, ImageUploadView,
    SearchSuggestionView
)
from .user_views import RegisterView, ProfileView, MyTokenObtainPairView, UserViewSet
from .notification_views import NotificationViewSet
from rest_framework_simplejwt.views import TokenRefreshView

# Router chính
router = DefaultRouter()
router.register(r'communities', CommunityViewSet, basename='community')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'users', UserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'notifications', NotificationViewSet, basename='notification')

# Nested router cho comments
posts_router = routers.NestedDefaultRouter(router, r'posts', lookup='post')
posts_router.register(r'comments', CommentViewSet, basename='post-comments')

# URL Patterns cuối cùng
urlpatterns = [
    path('', include(router.urls)),  # Router chính
    path('', include(posts_router.urls)),  # Router lồng cho comments
    path('search/suggestions/', SearchSuggestionView.as_view(), name='search-suggestions'),
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', ProfileView.as_view(), name='auth_profile'),
    path('upload-image/', ImageUploadView.as_view(), name='image-upload'),
]