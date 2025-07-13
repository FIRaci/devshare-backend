from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from posts.models import Post, Tag, Comment
from communities.models import Community
from users.models import CustomUser, Profile
from notifications.models import Notification

# Base Serializer for User-Related Logic
class BaseUserRelatedSerializer(serializers.ModelSerializer):
    """Base serializer for user-related logic."""
    def _check_user_relation(self, obj, field):
        user = self.context.get('request').user
        return user.is_authenticated and getattr(obj, field).filter(id=user.id).exists()

# Profile Serializer
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']

# User Serializer
class UserSerializer(BaseUserRelatedSerializer):
    profile = ProfileSerializer(read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'profile', 'is_staff', 'followers_count', 'following_count', 'is_following']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data.get('password')
        )

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_is_following(self, obj):
        return self._check_user_relation(obj, 'followers')

# Token Serializer
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user, context={'request': self.context.get('request')}).data
        return data

# Community Serializer
class CommunitySerializer(BaseUserRelatedSerializer):
    owner = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_muted = serializers.SerializerMethodField()
    is_notified = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ['id', 'name', 'description', 'owner', 'member_count', 'created_at', 'is_member', 'is_owner', 'is_muted', 'is_notified']
        read_only_fields = ['owner']

    def get_member_count(self, obj):
        return obj.members.count()

    def get_is_member(self, obj):
        return self._check_user_relation(obj, 'members')

    def get_is_owner(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and obj.owner == user

    def get_is_muted(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated and hasattr(user, 'profile'):
            return user.profile.muted_communities.filter(pk=obj.id).exists()
        return False

    def get_is_notified(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated and hasattr(user, 'profile'):
            return user.profile.notified_communities.filter(pk=obj.id).exists()
        return False

# Tag Serializer
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

# Comment Serializer
class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'parent']
        read_only_fields = ['post', 'author']

# Base Post Serializer
class BasePostSerializer(BaseUserRelatedSerializer):
    community = CommunitySerializer(read_only=True)
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    score = serializers.IntegerField(read_only=True)
    is_saved = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'community', 'author', 'title', 'content', 'image_url', 'created_at',
            'tags', 'score', 'upvotes', 'downvotes', 'is_saved', 'user_vote'
        ]

    def get_is_saved(self, obj):
        return self._check_user_relation(obj, 'saved_by_users')

    def get_user_vote(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            if obj.upvotes.filter(id=user.id).exists():
                return 1
            if obj.downvotes.filter(id=user.id).exists():
                return -1
        return None

# Post List Serializer
class PostListSerializer(BasePostSerializer):
    comment_count = serializers.SerializerMethodField()

    class Meta(BasePostSerializer.Meta):
        fields = BasePostSerializer.Meta.fields + ['comment_count']

    def get_comment_count(self, obj):
        return obj.comments.count()

# Post Detail Serializer
class PostDetailSerializer(BasePostSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(BasePostSerializer.Meta):
        fields = BasePostSerializer.Meta.fields + ['comments']

# Post Create/Update Serializer
class PostCreateUpdateSerializer(serializers.ModelSerializer):
    community_id = serializers.PrimaryKeyRelatedField(
        queryset=Community.objects.all(), source='community', write_only=True
    )

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'image_url', 'community_id']

# Notification Serializer
class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'actor', 'verb', 'target_id', 'is_read', 'timestamp']

# Suggestion Serializers
class PostSuggestionSerializer(serializers.ModelSerializer):
    community_name = serializers.CharField(source='community.name')

    class Meta:
        model = Post
        fields = ['id', 'title', 'community_name']

class CommunitySuggestionSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source='profile.avatar', read_only=True)

    class Meta:
        model = Community
        fields = ['id', 'name', 'avatar']

class UserSuggestionSerializer(serializers.ModelSerializer):
    avatar = serializers.URLField(source='profile.avatar', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'avatar']