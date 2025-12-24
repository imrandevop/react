#!/usr/bin/env python3
"""
Test script for Supabase Storage Integration
Tests the new upload URL generation endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

# First, login to get token
print("="*70)
print("Testing Supabase Storage Integration")
print("="*70)

# Step 1: Login
print("\n1. Logging in...")
login_data = {
    "userId": "550e8400-e29b-41d4-a716-446655440000",  # Example UUID
    "localBody": "Test City",
    "pincode": "123456"
}

response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
if response.status_code == 200:
    data = response.json()
    token = data['data']['token']
    print(f"✓ Login successful. Token: {token[:20]}...")
else:
    print(f"✗ Login failed: {response.status_code}")
    print(response.text)
    exit(1)

# Step 2: Generate signed upload URL
print("\n2. Generating signed upload URL...")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

upload_url_data = {
    "filename": "test-image.jpg",
    "content_type": "image/jpeg"
}

response = requests.post(f"{BASE_URL}/storage/upload-url", json=upload_url_data, headers=headers)
if response.status_code == 200:
    data = response.json()
    print("✓ Signed URL generated successfully!")
    print(f"  Upload URL: {data['data']['upload_url'][:60]}...")
    print(f"  Public URL: {data['data']['public_url'][:60]}...")
    print(f"  File Path: {data['data']['file_path']}")
    print(f"  Expires In: {data['data']['expires_in']} seconds")
else:
    print(f"✗ Failed to generate upload URL: {response.status_code}")
    print(response.text)
    exit(1)

# Step 3: Test creating a post with image URLs
print("\n3. Testing post creation with image URLs...")
public_url = data['data']['public_url']

post_data = {
    "category": "NEWS",
    "headline": "Test Post with Supabase Image",
    "description": "This post uses an image from Supabase Storage",
    "image_urls": [public_url]
}

response = requests.post(f"{BASE_URL}/posts/", json=post_data, headers=headers)
if response.status_code == 201:
    post_data = response.json()
    print("✓ Post created successfully with Supabase image URL!")
    print(f"  Post ID: {post_data['data']['id']}")
    print(f"  Image URLs: {post_data['data']['imageUrls']}")
else:
    print(f"✗ Failed to create post: {response.status_code}")
    print(response.text)

print("\n" + "="*70)
print("Supabase Integration Test Complete!")
print("="*70)
