#!/usr/bin/env python
"""Test what the feed API is actually returning"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'react_app.settings')
django.setup()

from basic.models import Post, User
from basic.serializers import PostSerializer
from django.test import RequestFactory

# Get a user and latest post
user = User.objects.first()
post = Post.objects.latest('created_at')

# Simulate a request
factory = RequestFactory()
request = factory.get('/api/feed')
request.user = user

from rest_framework.request import Request as DRFRequest
drf_request = DRFRequest(request)

# Serialize the post (same as feed API does)
serializer = PostSerializer(post, context={'request': drf_request})

print("=" * 80)
print(f"Post ID: {post.id}")
print(f"Post headline: {post.headline}")
print(f"Number of images: {post.images.count()}")
print("=" * 80)

import json
print("\nSerialized data (as returned by API):")
print(json.dumps(serializer.data, indent=2))

print("\n" + "=" * 80)
print("Image URLs being returned:")
for url in serializer.data.get('imageUrls', []):
    print(f"  - {url}")
