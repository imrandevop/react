#!/usr/bin/env python3
"""
Test script to reproduce multiple image upload errors
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

# Step 1: Login
print("="*70)
print("Testing Multiple Image Upload")
print("="*70)

print("\n1. Logging in...")
login_data = {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
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

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Test 1: Multiple image URLs (Supabase method)
print("\n2. Testing multiple image URLs (Supabase)...")
print("   Generating 3 upload URLs...")

image_urls = []
for i in range(3):
    upload_url_data = {
        "filename": f"test-image-{i+1}.jpg",
        "content_type": "image/jpeg"
    }

    response = requests.post(f"{BASE_URL}/storage/upload-url", json=upload_url_data, headers=headers)
    if response.status_code == 200:
        data = response.json()
        public_url = data['data']['public_url']
        image_urls.append(public_url)
        print(f"   ✓ URL {i+1} generated: {public_url[:50]}...")
    else:
        print(f"   ✗ Failed to generate URL {i+1}: {response.status_code}")
        print(f"   Response: {response.text}")

if len(image_urls) == 3:
    print(f"\n   Creating post with {len(image_urls)} image URLs...")
    post_data = {
        "category": "PROBLEM",
        "headline": "Test Problem with Multiple Images",
        "description": "Testing multiple image upload functionality",
        "image_urls": image_urls
    }

    response = requests.post(f"{BASE_URL}/posts/", json=post_data, headers=headers)
    print(f"\n   Response Status: {response.status_code}")
    print(f"   Response Body:")
    print(json.dumps(response.json(), indent=2))

    if response.status_code == 201:
        print("\n   ✓ SUCCESS! Post created with multiple image URLs")
        post_id = response.json()['data']['id']
        print(f"   Post ID: {post_id}")
        print(f"   Image count: {len(response.json()['data']['imageUrls'])}")
    else:
        print("\n   ✗ FAILED! Error creating post with multiple images")

# Test 2: File-based upload (if media directory exists)
print("\n" + "="*70)
print("3. Testing file-based multiple image upload...")

# Check if we have test images
media_dir = Path("media")
if not media_dir.exists():
    print("   Media directory doesn't exist. Skipping file-based test.")
else:
    # We would need actual image files for this test
    print("   Note: This would require actual image files to test")
    print("   You can test this manually by sending multipart/form-data")
    print("   with multiple 'images' fields")

print("\n" + "="*70)
print("Test Complete!")
print("="*70)
