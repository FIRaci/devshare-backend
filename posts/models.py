from django.db import models
from django.conf import settings

# Giả sử các model khác của bạn ở đây...

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    # SỬA LỖI: Thêm trường image_url vào đây
    image_url = models.URLField(max_length=500, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    community = models.ForeignKey('communities.Community', on_delete=models.CASCADE, related_name='posts')
    
    tags = models.ManyToManyField('Tag', blank=True)
    
    upvotes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='upvoted_posts', blank=True)
    downvotes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='downvoted_posts', blank=True)

    @property
    def score(self):
        return self.upvotes.count() - self.downvotes.count()

    def __str__(self):
        return self.title

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    def __str__(self):
        return f'Comment by {self.author} on {self.post}'
