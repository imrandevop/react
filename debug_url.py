#!/usr/bin/env python
"""Debug what Supabase returns"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'react_app.settings')
django.setup()

from basic.supabase_storage import get_supabase_client
from django.conf import settings

client = get_supabase_client()
bucket = settings.SUPABASE_BUCKET_NAME

# Test with an existing file path
url = client.storage.from_(bucket).get_public_url("posts/20251229-18095e1b.jpg")

print(f"Type: {type(url)}")
print(f"Raw URL repr: {repr(url)}")
print(f"Length: {len(url)}")
print(f"Ends with ?: {url.endswith('?')}")
print(f"Stripped: {repr(url.strip())}")
print(f"After rstrip('?'): {repr(url.strip().rstrip('?'))}")
