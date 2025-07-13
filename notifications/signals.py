from django.db.models.signals import post_save
from django.dispatch import receiver
from posts.models import Comment
from .models import Notification

@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        recipient = instance.post.author
        # Chỉ tạo thông báo nếu người nhận chưa tắt thông báo từ community này và không phải là tác giả bình luận
        if instance.author != recipient and not recipient.profile.muted_communities.filter(pk=instance.post.community.pk).exists():
            Notification.objects.create(
                recipient=recipient,
                actor=instance.author,
                verb=f'commented on your post: "{instance.post.title[:30]}..."',
                target_id=instance.post.id,
            )