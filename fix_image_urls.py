#!/usr/bin/env python
"""
Quick script to clean whitespace from image URLs in database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'react_app.settings')
django.setup()

from basic.models import PostImage

# Fix all image URLs with trailing whitespace
updated = 0
for img in PostImage.objects.all():
    if img.image_url:
        cleaned = img.image_url.strip()
        if cleaned != img.image_url:
            img.image_url = cleaned
            img.save()
            updated += 1
            print(f"✓ Fixed image {img.id}")

print(f"\n✅ Updated {updated} image URLs")
