from django.db import models
from django.conf import settings
import uuid

from .storage import MixedMediaCloudinaryStorage

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/uploads/user_<username>/<filename>
    return 'uploads/{0}/{1}'.format(instance.owner.username, filename)

class File(models.Model):
    CONTENT_CHOICES=[
        ('image','Image'),
        ('video','Video'),
        ('document','Document'),
        ('audio','Audio'),
        ('other','OTHER'),
        ('all','ALL'),
    ]
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='files')
    file = models.FileField(upload_to=user_directory_path, storage=MixedMediaCloudinaryStorage())
    original_filename = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=20,choices=CONTENT_CHOICES,default='all')
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


