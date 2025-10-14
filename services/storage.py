"""File storage service for managing uploaded images."""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from supabase import create_client, Client

class StorageService:
    """Handles file storage operations with environment-based storage."""
    
    def __init__(self, upload_folder):
        """Initialize storage service."""
        self.upload_folder = upload_folder
        self.env = os.getenv('FLASK_ENV', 'development')
        
        if self.env == 'production':
            # Initialize Supabase for production
            supabase_url = os.getenv('PROJECT_URL')
            supabase_key = os.getenv('SERVICE_ROLE')
            self.bucket = os.getenv('SUPABASE_BUCKET', 'images')
            
            if supabase_url and supabase_key:
                self.supabase: Client = create_client(supabase_url, supabase_key)
            else:
                raise ValueError("Supabase credentials not found in production")
        else:
            # Use local storage for development
            os.makedirs(upload_folder, exist_ok=True)
    
    def _upload_to_supabase(self, unique_filename, file_data, content_type):
        """Internal method to upload to Supabase."""
        self.supabase.storage.from_(self.bucket).upload(
            unique_filename,
            file_data,
            file_options={"content-type": content_type}
        )
        return self.supabase.storage.from_(self.bucket).get_public_url(unique_filename)
    
    def save_file(self, file, user_id):
        """
        Save uploaded file (local or Supabase based on environment).
        
        Args:
            file: FileStorage object from Flask request
            user_id: ID of the user uploading the file
            
        Returns:
            tuple: (filepath/url, unique_filename)
        """
        filename = secure_filename(file.filename)
        unique_filename = f"{user_id}_{uuid.uuid4().hex}_{filename}"
        
        if self.env == 'production':
            # Upload to Supabase Storage asynchronously
            file_data = file.read()
            file.seek(0)
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self._upload_to_supabase,
                    unique_filename,
                    file_data,
                    file.content_type
                )
                public_url = future.result()
            
            return public_url, unique_filename
        else:
            # Save to local filesystem with streaming
            filepath = os.path.join(self.upload_folder, unique_filename)
            
            # Stream file in chunks to avoid loading entire file in memory
            with open(filepath, 'wb') as f:
                while True:
                    chunk = file.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    f.write(chunk)
            
            file.seek(0)  # Reset file pointer for potential reuse
            return filepath, unique_filename
    
    def delete_file(self, filepath):
        """Delete file from storage."""
        if self.env == 'production':
            # Extract filename from URL
            filename = filepath.split('/')[-1]
            self.supabase.storage.from_(self.bucket).remove([filename])
        else:
            # Delete from local filesystem
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def file_exists(self, filepath):
        """Check if file exists in storage."""
        if self.env == 'production':
            # For Supabase, assume file exists if we have a URL
            return bool(filepath)
        else:
            return os.path.exists(filepath)
