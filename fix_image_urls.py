#!/usr/bin/env python
"""
Quick script to clean whitespace and trailing ? from image URLs in database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'react_app.settings')
django.setup()

from basic.models import PostImage

# Fix all image URLs with trailing whitespace or ?
updated = 0
for img in PostImage.objects.all():
    if img.image_url:
        cleaned = img.image_url.strip().rstrip('?')
        if cleaned != img.image_url:
            print(f"Before: {repr(img.image_url)}")
            print(f"After:  {repr(cleaned)}")
            img.image_url = cleaned
            img.save()
            updated += 1
            print(f"✓ Fixed image {img.id}\n")

print(f"\n✅ Updated {updated} image URLs")
