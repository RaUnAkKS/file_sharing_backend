from django.utils import timezone
from sharing.models import ShareLink
from files.models import File



def check_validation(share_link):
    if share_link.is_active==False:
        return False
    if share_link.expires_at < timezone.now():
        return False
    if share_link.download_count >= share_link.max_downloads:
        return False
    share_link.download_count += 1
    share_link.save(update_fields=['download_count'])
    return True