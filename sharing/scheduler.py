from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from .tasks import expire_old_links
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django_apscheduler.models import DjangoJobExecution
import sys

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    scheduler.add_job(
        expire_old_links, 
        'interval', 
        minutes=10, 
        name='Expire Links', 
        jobstore='default',
        id='expire_links_job',
        replace_existing=True
    )
    
    register_events(scheduler)
    scheduler.start()
    print("Scheduler started...", file=sys.stdout)
