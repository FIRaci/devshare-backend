from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.models import Profile, CustomUser
from posts.models import Post, Tag, Comment
from communities.models import Community
from notifications.models import Notification

# Serializer cho Notification
class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'actor', 'verb', 'target_id', 'is_read', 'timestamp']

    def get_actor(self, obj):
        return UserSerializer(obj.actor, context=self.context).data

# Serializer cho Profile
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']

# Serializer cho User (hiển thị và đăng ký)
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'profile', 'followers_count', 'following_count', 'is_following']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_is_following(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return obj.followers.filter(id=user.id).exists()  # Sửa để kiểm tra followers
        return False

# Serializer tùy chỉnh cho đăng nhập
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializer(self.user, context={'request': self.context.get('request')})
        data.update({'user': serializer.data})
        return data

# Serializer cho Community
class CommunitySerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ['id', 'name', 'description', 'owner', 'member_count', 'created_at', 'is_member']

    def get_member_count(self, obj):
        return obj.members.count()

    def get_is_member(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return obj.members.filter(id=user.id).exists()
        return False

# Serializer cho Tag
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

# Serializer cho Comment
class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'parent']
        read_only_fields = ['author']

# Serializer cơ sở cho Post
class BasePostSerializer(serializers.ModelSerializer):
    community = CommunitySerializer(read_only=True)
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    score = serializers.IntegerField(read_only=True)
    is_saved = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'community', 'author', 'title', 'content', 'created_at',
            'tags', 'score', 'upvotes', 'downvotes', 'is_saved', 'user_vote'
        ]

    def get_is_saved(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return obj.saved_by_users.filter(id=user.id).exists()
        return False

    def get_user_vote(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            if obj.upvotes.filter(id=user.id).exists():
                return 1
            if obj.downvotes.filter(id=user.id).exists():
                return -1
        return None

# Serializer cho danh sách bài viết
class PostListSerializer(BasePostSerializer):
    comment_count = serializers.SerializerMethodField()

    class Meta(BasePostSerializer.Meta):
        fields = BasePostSerializer.Meta.fields + ['comment_count']

    def get_comment_count(self, obj):
        return obj.comments.count()

# Serializer cho chi tiết bài viết
class PostDetailSerializer(BasePostSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(BasePostSerializer.Meta):
        fields = BasePostSerializer.Meta.fields + ['comments']

# Serializer cho tạo/cập nhật bài viết
class PostCreateUpdateSerializer(serializers.ModelSerializer):
    community_id = serializers.PrimaryKeyRelatedField(
        queryset=Community.objects.all(), source='community', write_only=True
    )

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'community_id']