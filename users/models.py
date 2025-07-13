from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
# Bạn cần import Community để sử dụng trong ManyToManyField
from communities.models import Community
from posts.models import Post

class CustomUser(AbstractUser):
    # SỬA LỖI: Xóa trường `joined_communities`.
    # Mối quan hệ này nên được định nghĩa một lần duy nhất trong model `Community`
    # (thông qua trường `members`). Việc định nghĩa ở cả hai model gây ra lỗi xung đột.
    # Code trong views và serializers vẫn sẽ hoạt động nếu `Community.members` có
    # `related_name='joined_communities'`.
    saved_posts = models.ManyToManyField(Post, related_name='saved_by_users', blank=True)
    following = models.ManyToManyField('self', through='UserFollowing', related_name='followers', symmetrical=False, blank=True)

class UserFollowing(models.Model):
    user_from = models.ForeignKey(CustomUser, related_name='rel_from_set', on_delete=models.CASCADE)
    user_to = models.ForeignKey(CustomUser, related_name='rel_to_set', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created']
        constraints = [models.UniqueConstraint(fields=['user_from', 'user_to'], name='unique_followers')]
    def __str__(self):
        return f"{self.user_from} follows {self.user_to}"

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    avatar = models.URLField(max_length=500, blank=True, null=True)
    
    muted_communities = models.ManyToManyField(Community, blank=True, related_name='muted_by_profiles')
    notified_communities = models.ManyToManyField(Community, blank=True, related_name='notified_profiles')

    def __str__(self):
        return f'{self.user.username} Profile'

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    # Đảm bảo profile được tạo nếu chưa tồn tại
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
    instance.profile.save()
