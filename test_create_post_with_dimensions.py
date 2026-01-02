#!/usr/bin/env python
"""Test creating a post with image dimensions"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'react_app.settings')
django.setup()

from basic.models import Post, User
from basic.serializers import PostCreateUpdateSerializer
from django.test import RequestFactory
from rest_framework.request import Request as DRFRequest

# Get a user
user = User.objects.first()

# Test image URL (use an existing one)
test_url = "https://fhyorgkvdamjuboftetp.supabase.co/storage/v1/object/public/react/posts/20251229-903ec859.jpg"

# Create request with authenticated user
from rest_framework.test import force_authenticate
factory = RequestFactory()
request = factory.post('/api/posts/')
force_authenticate(request, user=user)
drf_request = DRFRequest(request)

# Test data
data = {
    'category': 'NEWS',
    'headline': 'Test dimensions',
    'description': 'Testing image dimensions feature',
    'image_urls': [test_url]
}

print("Creating post with image dimensions...")
print(f"Image URL: {test_url}")

serializer = PostCreateUpdateSerializer(data=data, context={'request': drf_request})

if serializer.is_valid():
    post = serializer.save()
    print(f"\n✅ Post created: ID {post.id}")

    # Check if dimensions were saved
    for img in post.images.all():
        print(f"\nImage dimensions:")
        print(f"  Width: {img.width}")
        print(f"  Height: {img.height}")
        print(f"  URL: {img.image_url}")

        if img.width and img.height:
            print(f"  ✅ Dimensions successfully fetched!")
        else:
            print(f"  ❌ Dimensions not fetched")
else:
    print(f"\n❌ Validation errors: {serializer.errors}")
