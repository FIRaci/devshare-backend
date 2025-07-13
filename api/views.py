import re
from rest_framework import viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count
import cloudinary.uploader
from posts.models import Post, Tag, Comment
from communities.models import Community
from users.models import CustomUser
from .serializers import (
    PostListSerializer, PostDetailSerializer, PostCreateUpdateSerializer,
    TagSerializer, CommentSerializer, CommunitySerializer, UserSerializer,
    PostSuggestionSerializer, CommunitySuggestionSerializer, UserSuggestionSerializer
)
from .permissions import IsOwnerOrReadOnly, IsAdminUser

# Helper Functions
def get_tags_from_ai(text):
    """Extract tags from text based on predefined list."""
    potential_tags = ['python', 'django', 'react', 'ai', 'database', 'javascript', 'next.js', 'typescript']
    return list(set(tag for tag in potential_tags if tag.lower() in text.lower()))

# Base ViewSet for Social Features
class BaseSocialViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    def _toggle_vote(self, request, pk, vote_field, opposite_field, status_str):
        obj = self.get_object()
        user = request.user
        getattr(obj, opposite_field).remove(user)
        if user in getattr(obj, vote_field).all():
            getattr(obj, vote_field).remove(user)
            return Response({'status': f'un{status_str}', 'score': obj.score})
        getattr(obj, vote_field).add(user)
        return Response({'status': status_str, 'score': obj.score})
    def _toggle_save(self, request, pk, field, status_str):
        obj = self.get_object()
        user = request.user
        if obj in getattr(user, field).all():
            getattr(user, field).remove(obj)
            return Response({'status': f'un{status_str}'})
        getattr(user, field).add(obj)
        return Response({'status': status_str})
    def _paginate_response(self, queryset, serializer_class):
        page = self.paginate_queryset(queryset)
        serializer = serializer_class(page or queryset, many=True, context={'request': self.request})
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

# Image Upload View
class ImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            upload_data = cloudinary.uploader.upload(file_obj)
            return Response({'url': upload_data['secure_url']}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Post ViewSet
class PostViewSet(BaseSocialViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content', 'tags__name']

    def get_serializer_class(self):
        """Chọn Serializer phù hợp với từng action."""
        if self.action == 'list':
            return PostListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateUpdateSerializer
        return PostDetailSerializer

    def get_queryset(self):
        """Lọc bài viết theo query params."""
        queryset = super().get_queryset()
        filters = {
            'community__name__iexact': self.request.query_params.get('community__name'),
            'author__username__iexact': self.request.query_params.get('author__username')
        }
        return queryset.filter(**{k: v for k, v in filters.items() if v is not None})

    def perform_create(self, serializer):
        """Tự động gán author, tạo tag, và trích xuất image_url từ content."""
        post = serializer.save(author=self.request.user)
        
        # Trích xuất URL ảnh đầu tiên từ content và lưu lại
        content = post.content
        image_match = re.search(r'!\[.*?\]\((.*?)\)', content)
        if image_match:
            post.image_url = image_match.group(1)
            post.save()

        # Tạo và gán tag
        text_content = f"{post.title} {post.content}"
        tags = [Tag.objects.get_or_create(name=tag)[0] for tag in get_tags_from_ai(text_content)]
        post.tags.set(tags)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def home_feed(self, request):
        """API cho trang chủ: feed từ community đã join (nếu login) hoặc bài hot (nếu khách)."""
        if request.user.is_authenticated:
            joined_communities = request.user.joined_communities.all()
            if not joined_communities.exists():
                return self.get_paginated_response(self.paginate_queryset([]))
            queryset = Post.objects.filter(community__in=joined_communities).order_by('-created_at')
        else:
            queryset = Post.objects.annotate(
                calculated_score=Count('upvotes') - Count('downvotes')
            ).order_by('-calculated_score', '-created_at')
        return self._paginate_response(queryset, PostListSerializer)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def saved(self, request):
        """Lấy danh sách bài viết đã lưu."""
        saved_posts = request.user.saved_posts.all().order_by('-created_at')
        return self._paginate_response(saved_posts, PostListSerializer)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upvote(self, request, pk=None):
        return self._toggle_vote(request, pk, 'upvotes', 'downvotes', 'upvoted')

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def downvote(self, request, pk=None):
        return self._toggle_vote(request, pk, 'downvotes', 'upvotes', 'downvoted')

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def save(self, request, pk=None):
        return self._toggle_save(request, pk, 'saved_posts', 'saved')

# Tag ViewSet
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# Comment ViewSet
class CommentViewSet(BaseSocialViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Lọc comment theo post_id từ URL (nếu có)."""
        post_id = self.kwargs.get('post_pk')
        if post_id:
            return Comment.objects.filter(post_id=post_id)
        return super().get_queryset()

    def perform_create(self, serializer):
        """Gán comment cho đúng bài post và user."""
        post_id = self.kwargs.get('post_pk')
        if post_id:
            serializer.save(author=self.request.user, post_id=post_id)
        else:
            serializer.save(author=self.request.user)

# Community ViewSet
class CommunityViewSet(BaseSocialViewSet):
    queryset = Community.objects.all().order_by('name')
    serializer_class = CommunitySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    lookup_field = 'name'

    def get_permissions(self):
        """Chỉ admin được xóa community."""
        if self.action == 'destroy':
            return [IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        """Lọc community theo query params."""
        queryset = super().get_queryset()
        if self.request.query_params.get('joined') == 'true' and self.request.user.is_authenticated:
            queryset = queryset.filter(members=self.request.user)
        return queryset

    def perform_create(self, serializer):
        """Tự động gán owner và thêm user vào members khi tạo community."""
        community = serializer.save(owner=self.request.user)
        community.members.add(self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def join(self, request, name=None):
        community = self.get_object()
        community.members.add(request.user)
        return Response({'status': 'joined'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def leave(self, request, name=None):
        community = self.get_object()
        if request.user == community.owner:
            return Response({'error': 'Owner cannot leave the community'}, status=status.HTTP_400_BAD_REQUEST)
        community.members.remove(request.user)
        return Response({'status': 'left'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_mute(self, request, name=None):
        community = self.get_object()
        profile = request.user.profile
        if community in profile.muted_communities.all():
            profile.muted_communities.remove(community)
            return Response({'status': 'unmuted'})
        profile.muted_communities.add(community)
        return Response({'status': 'muted'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_notifications(self, request, name=None):
        community = self.get_object()
        profile = request.user.profile
        if community in profile.notified_communities.all():
            profile.notified_communities.remove(community)
            return Response({'status': 'notifications_off'})
        profile.notified_communities.add(community)
        return Response({'status': 'notifications_on'})

    @action(detail=True, methods=['get'])
    def members(self, request, name=None):
        community = self.get_object()
        members = community.members.all()
        page = self.paginate_queryset(members)
        serializer = UserSerializer(page or members, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

# Search Suggestion View
class SearchSuggestionView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response({"posts": [], "communities": [], "users": []})
        limit = 5
        posts = Post.objects.filter(title__icontains=query)[:limit]
        communities = Community.objects.filter(name__icontains=query)[:limit]
        users = CustomUser.objects.filter(username__icontains=query)[:limit]
        return Response({
            "posts": PostSuggestionSerializer(posts, many=True).data,
            "communities": CommunitySuggestionSerializer(communities, many=True).data,
            "users": UserSuggestionSerializer(users, many=True).data
        })