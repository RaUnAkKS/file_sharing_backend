from django.apps import AppConfig


class SharingConfig(AppConfig):
    name = 'sharing'

    def ready(self):
        import os
        # Ensure it only runs once in development (reloader)
        if os.environ.get('RUN_MAIN') or not os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('.settings'):
            # The second condition is a fallback for production (Render) where RUN_MAIN might not be set by runserver
            # But in production usually only one worker starts. 
            # Sticking to just RUN_MAIN is risky for production if gunicorn doesn't set it.
            # Gunicorn doesn't set RUN_MAIN. 
            # However, the error is 'database is locked', which is specific to SQLite handling concurrency bad.
            # In production (Render), if using SQLite, same issue might occur if multiple workers.
            # But user is likely using SQLite on Render too (disk).
            
            # Simplified: Use a try-except block to just log if locked.
            # But the best fix for 'runserver' double-run is RUN_MAIN.
            from . import scheduler
            try:
                scheduler.start()
            except Exception as e:
                print(f"Scheduler failed to start: {e}")
