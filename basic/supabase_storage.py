"""
Supabase Storage Helper Module
Provides utilities for generating signed upload URLs and managing files in Supabase Storage
"""

import os
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client with service role key for admin operations
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    
    if not url or not key:
        raise ValueError("Supabase URL and Service Role Key must be configured in settings")
    
    return create_client(url, key)


def generate_unique_filename(original_filename: str, prefix: str = "posts") -> str:
    """
    Generate a unique filename with UUID to prevent collisions
    
    Args:
        original_filename: Original filename from client
        prefix: Folder prefix (default: "posts")
    
    Returns:
        Unique file path in format: prefix/uuid-filename.ext
    """
    # Extract file extension
    if '.' in original_filename:
        name, ext = original_filename.rsplit('.', 1)
        ext = ext.lower()
    else:
        name = original_filename
        ext = 'jpg'  # Default extension
    
    # Generate unique filename with timestamp and UUID
    timestamp = datetime.now().strftime('%Y%m%d')
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{timestamp}-{unique_id}.{ext}"
    
    # Return path with prefix
    return f"{prefix}/{filename}"


def generate_signed_upload_url(file_path: str, expiry_seconds: int = 3600) -> dict:
    """
    Generate a signed URL for uploading files to Supabase Storage
    
    Args:
        file_path: Path where file will be stored in bucket
        expiry_seconds: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        dict with:
            - signed_url: Pre-signed URL for upload
            - file_path: Path in the bucket
            - public_url: Public URL to access the file after upload
    """
    try:
        supabase = get_supabase_client()
        bucket_name = settings.SUPABASE_BUCKET_NAME
        
        # Create signed upload URL
        # Note: Supabase Python client uses create_signed_upload_url
        signed_url_response = supabase.storage.from_(bucket_name).create_signed_upload_url(file_path)
        
        # Get the signed URL from response
        signed_url = signed_url_response.get('signedURL') or signed_url_response.get('signed_url')
        
        # Generate public URL for the file
        public_url = get_public_url(file_path)
        
        return {
            "signed_url": signed_url,
            "file_path": file_path,
            "public_url": public_url,
            "expires_in": expiry_seconds
        }
    except Exception as e:
        raise Exception(f"Failed to generate signed upload URL: {str(e)}")


def get_public_url(file_path: str) -> str:
    """
    Get the public URL for a file in Supabase Storage
    
    Args:
        file_path: Path of file in bucket
    
    Returns:
        Public URL to access the file
    """
    try:
        supabase = get_supabase_client()
        bucket_name = settings.SUPABASE_BUCKET_NAME
        
        # Get public URL
        public_url_response = supabase.storage.from_(bucket_name).get_public_url(file_path)
        
        return public_url_response
    except Exception as e:
        raise Exception(f"Failed to get public URL: {str(e)}")


def delete_file(file_path: str) -> bool:
    """
    Delete a file from Supabase Storage
    
    Args:
        file_path: Path of file to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        bucket_name = settings.SUPABASE_BUCKET_NAME
        
        # Delete file
        supabase.storage.from_(bucket_name).remove([file_path])
        return True
    except Exception as e:
        print(f"Failed to delete file {file_path}: {str(e)}")
        return False


def validate_image_url(url: str) -> bool:
    """
    Validate if URL is from Supabase Storage bucket
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid Supabase Storage URL, False otherwise
    """
    if not url:
        return False
    
    # Check if URL contains Supabase domain and bucket name
    supabase_url = settings.SUPABASE_URL
    bucket_name = settings.SUPABASE_BUCKET_NAME
    
    return (supabase_url in url and bucket_name in url) or url.startswith('/media/')
