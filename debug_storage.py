
import os
import sys
import django
import requests
import io
import cloudinary.utils
from django.core.files.base import ContentFile

# Setup Django environment
# Assumes we are in the inner project directory where settings.py resides
# But sys.path needs the outer directory so 'file_sharing' package is visible.
sys.path.append(os.path.dirname(os.getcwd())) # Add parent directory to path

from dotenv import load_dotenv
env_path = os.path.join(os.getcwd(), '.env')
load_dotenv(env_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'file_sharing.settings')
django.setup()

from files.storage import MixedMediaCloudinaryStorage # Correct import now

def test_upload():
    print("--- Starting Storage Test ---")
    
    storage = MixedMediaCloudinaryStorage()
    
    # Test Data: A minimal valid GIF (1x1 pixel)
    gif_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xFF\xFF\xFF\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'
    
    file_name = "test_upload_debug_inner.gif"
    content = ContentFile(gif_content)
    
    # Save
    print(f"Uploading {file_name}...")
    saved_name = storage.save(file_name, content)
    print(f"Saved Name: {saved_name}")
    
    # Get URL with signature
    url, options = cloudinary.utils.cloudinary_url(
        saved_name,
        resource_type='raw',
        type='upload',
        sign_url=True 
    )
    print(f"Generated Signed URL: {url}")
    
    # Verify Access
    print(f"Testing access to URL: {url}")
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Verify Content: {response.content[:10]}")
        
        if response.status_code == 200:
            print("SUCCESS: File is accessible!")
        elif response.status_code == 401:
            print("FAILURE: 401 Unauthorized. Check permissions/ACL.")
            # Try signed URL?
            pass
        else:
            print(f"FAILURE: Unexpected status {response.status_code}")
            
    except Exception as e:
        print(f"ERROR accessing URL: {e}")

if __name__ == "__main__":
    test_upload()
