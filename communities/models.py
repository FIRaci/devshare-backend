from django.db import models
from django.conf import settings

class Community(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_communities')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_communities', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Communities"