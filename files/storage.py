from cloudinary_storage.storage import MediaCloudinaryStorage
import cloudinary.uploader
import os

class MixedMediaCloudinaryStorage(MediaCloudinaryStorage):
    """
    Storage class that forces 'auto' resource type to support images, videos, 
    and raw files interchangeably in a single field.
    """
    # Remove specific _upload method, instead override _save fully.
    def _save(self, name, content):
        """
        Store the file in Cloudinary with distinct handling for Image/Video vs Raw.
        For Images/Videos: Strip extension from public_id to avoid double extensions in URL.
        For Raw: Keep extension in public_id.
        """
        # Determine resource type and extension
        ext = name.split('.')[-1].lower() if '.' in name else ''
        
        resource_type = 'raw'
        if ext in ['mp4', 'mov', 'avi', 'webm', 'mkv']:
            resource_type = 'video'
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'ico']: # PDF removed from here
            resource_type = 'image'

        # Construct public_id
        # For image/video, Cloudinary handles extension automatically usually.
        # But if we pass it, it might double it. We strip it here.
        if resource_type in ['image', 'video']:
            public_id = os.path.splitext(name)[0]
        else:
            public_id = name
            
        # Cloudinary requires forward slashes for public_id
        public_id = public_id.replace('\\', '/')

        options = {
            'resource_type': resource_type, # Force explicit resource type
            'public_id': public_id,
            'unique_filename': False,
            'overwrite': True,
            'type': 'upload' # Explicitly set to 'upload' to ensure public access
        }

        print(f"DEBUG: Uploading {name} as {resource_type} with ID {public_id}") # DEBUG LOG
        
        # Ensure file pointer is at the beginning
        if hasattr(content, 'seek'):
            content.seek(0)
            
        # Log content size for debugging
        try:
            size = content.size
        except AttributeError:
            try:
                size = len(content)
            except:
                size = 'Unknown'
        print(f"DEBUG: Content size before read: {size}") # DEBUG LOG
        
        # Explicitly read content into memory to ensure data is available
        file_content = content.read()
        print(f"DEBUG: Read {len(file_content)} bytes into memory") # DEBUG LOG

        if len(file_content) == 0:
            print("ERROR: File content is empty after read!")
            
        import tempfile
        import shutil
        
        # Write to a temporary file on disk
        # Cloudinary's uploader is more reliable with file paths
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
            
        print(f"DEBUG: Wrote {len(file_content)} bytes to temporary file {tmp_path}") # DEBUG LOG
        
        try:
            # Perform upload using the file path
            # Passing as keyword argument 'file' to be explicit
            response = cloudinary.uploader.upload(file=tmp_path, **options)
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                print(f"DEBUG: Removed temporary file {tmp_path}") # DEBUG LOG
        
        print(f"DEBUG: Cloudinary Response Public ID: {response.get('public_id')}") # DEBUG LOG
        print(f"DEBUG: Full Response: {response}") # DEBUG LOG
        
        # Crucial: Return the ORIGINAL name (with extension) to Django
        # This ensures DB stores 'file.jpg', identifying the type correctly later.
        # But should we normalize this too? Django usually handles it.
        return name

    # Remove old _upload method (it's covered by _save now)
    
    def url(self, name):
        """
        Return the Cloudinary URL with the correct resource_type based on file extension.
        Reconstruct the public_id based on the extension logic used in _save.
        """
        import cloudinary.utils
        
        # Determine resource type (same logic as _save)
        ext = name.split('.')[-1].lower() if '.' in name else ''
        
        resource_type = 'raw'
        if ext in ['mp4', 'mov', 'avi', 'webm', 'mkv']:
            resource_type = 'video'
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'ico']: # PDF removed from here
            resource_type = 'image'
            
        # Reconstruct public_id used for upload
        if resource_type in ['image', 'video']:
            public_id = os.path.splitext(name)[0]
        else:
            public_id = name

        # Ensure forward slashes
        public_id = public_id.replace('\\', '/')

        # Determine Format
        # For 'image' and 'video', Cloudinary expects a format if the public_id doesn't have it.
        # We stripped the extension from public_id above, so we must re-attach it via the format option.
        format = ext
        
        # Exception: Raw files don't need format option as public_id has extension.
        if resource_type == 'raw':
             format = None

        # Generate URL
        print(f"DEBUG: Generating URL for {name} -> ID {public_id} (type {resource_type}, format {format})") # DEBUG LOG
        url, options = cloudinary.utils.cloudinary_url(
            public_id, 
            resource_type=resource_type, 
            format=format,
            type='upload' # Force 'upload' type for URL generation
        )
        print(f"DEBUG: Generated URL: {url}") # DEBUG LOG
        return url

    def _open(self, name, mode='rb'):
        """
        Retrieve file content from Cloudinary using the sanitized URL.
        This fixes issues where internal file paths contain backslashes on Windows,
        causing 400 Bad Request errors when accessing files directly (e.g. for zipping).
        """
        # Ensure we use the sanitized URL (replacing \ with /)
        url = self.url(name)
        
        # We need to fetch the content to return a file-like object
        import requests
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to fetch file {name} from {url}: {e}")
            # Return empty file or re-raise? Re-raising is safer to surface the error.
            raise IOError(f"Error opening {name}: {e}")
            
        from django.core.files.base import ContentFile
        return ContentFile(response.content, name=name)
