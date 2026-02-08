from django.utils import timezone
from .models import ShareLink
from django.db.models import F

def expire_old_links():
    now = timezone.now()
    expired_time = ShareLink.objects.filter(is_active=True, expires_at__lt=now)
    expired_limit = ShareLink.objects.filter(is_active=True, download_count__gte=F('max_downloads'))

    count_time = expired_time.update(is_active=False)
    count_limit = expired_limit.update(is_active=False)
    
    if count_time > 0 or count_limit > 0:
        print(f"Expired {count_time} links due to time and {count_limit} due to limits.")
