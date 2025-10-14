"""File storage service for managing uploaded images."""
import os
import uuid
from werkzeug.utils import secure_filename

class StorageService:
    """Handles file storage operations for uploaded images."""
    
    def __init__(self, upload_folder):
        """Initialize storage service with upload directory."""
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def save_file(self, file, user_id):
        """
        Save uploaded file with unique filename.
        
        Args:
            file: FileStorage object from Flask request
            user_id: ID of the user uploading the file
            
        Returns:
            tuple: (filepath, unique_filename)
        """
        filename = secure_filename(file.filename)
        unique_filename = f"{user_id}_{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(self.upload_folder, unique_filename)
        file.save(filepath)
        return filepath, unique_filename
    
    def delete_file(self, filepath):
        """Delete file from storage if it exists."""
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def file_exists(self, filepath):
        """Check if file exists in storage."""
        return os.path.exists(filepath)
