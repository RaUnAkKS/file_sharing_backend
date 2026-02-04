from django.db import models
import uuid
from files.models import File
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def default_expiry():
    return timezone.now() + timedelta(hours=3)

class ShareLink(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    files = models.ManyToManyField(File)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    expires_at = models.DateTimeField(default=default_expiry)
    max_downloads = models.IntegerField(default=1)
    download_count = models.IntegerField(default=0)
    password = models.CharField(max_length=100,blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
