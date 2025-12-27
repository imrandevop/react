# Frontend Image Upload Guide

## Overview

**Method:** Supabase URL-based upload (3-step process)
**Content-Type:** JSON only
**Max Images:** 10 per post

---

## Image Upload Flow

### **Step 1: Get Upload URL from Backend**

**Endpoint:** `POST /api/storage/upload-url`

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "filename": "my-image.jpg",
  "content_type": "image/jpeg"
}
```

**Response (200):**
```json
{
  "data": {
    "upload_url": "https://supabase.co/storage/v1/object/upload/signed/...",
    "file_path": "post_images/uuid-timestamp-my-image.jpg",
    "public_url": "https://supabase.co/storage/v1/object/public/post_images/uuid-timestamp-my-image.jpg",
    "expires_in": 3600
  }
}
```

**Notes:**
- `upload_url` - Use this to upload the actual image file (expires in 1 hour)
- `public_url` - Save this URL to send in Step 3
- Call this once per image

---

### **Step 2: Upload Image to Supabase**

**Endpoint:** Use `upload_url` from Step 1

**Method:** `PUT`

**Headers:**
```
Content-Type: image/jpeg  (or image/png, etc.)
```

**Body:** Raw image file bytes

**Response (200):**
```json
{
  "Key": "post_images/uuid-timestamp-my-image.jpg"
}
```

**Notes:**
- Upload directly to Supabase (not your backend)
- No authorization header needed
- Send raw image bytes

---

### **Step 3: Create Post with Image URLs**

**Endpoint:** `POST /api/posts/`

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "category": "PROBLEM",
  "headline": "Issue with water supply",
  "description": "Detailed description here",
  "image_urls": [
    "https://supabase.co/storage/v1/object/public/post_images/image1.jpg",
    "https://supabase.co/storage/v1/object/public/post_images/image2.jpg"
  ]
}
```

**Field Requirements:**
- `category` - **Required**. Options: `"NEWS"`, `"UPDATE"`, `"PROBLEM"`, `"ADVERTISEMENT"`
- `headline` - Optional (except for NEWS/UPDATE)
- `description` - **Required**
- `image_urls` - **Required for PROBLEM category**. Array of URLs from Step 2. Max 10 URLs.

**Response (201):**
```json
{
  "status": 201,
  "data": {
    "id": "post-uuid",
    "user": {
      "id": "user-uuid",
      "localBody": "City Name",
      "pincode": "123456"
    },
    "category": "PROBLEM",
    "headline": "Issue with water supply",
    "description": "Detailed description here",
    "imageUrls": [
      "https://supabase.co/storage/v1/object/public/post_images/image1.jpg",
      "https://supabase.co/storage/v1/object/public/post_images/image2.jpg"
    ],
    "upvotes": 0,
    "downvotes": 0,
    "commentsCount": 0,
    "created_at": "2025-12-27T11:30:00Z",
    "hasUpvoted": false,
    "hasDownvoted": false
  }
}
```

---

## Complete Example: Upload 2 Images

### **1. Get first upload URL**
```
POST /api/storage/upload-url
Body: {"filename": "photo1.jpg", "content_type": "image/jpeg"}
Response: {"data": {"upload_url": "URL_1", "public_url": "PUBLIC_URL_1", ...}}
```

### **2. Get second upload URL**
```
POST /api/storage/upload-url
Body: {"filename": "photo2.jpg", "content_type": "image/jpeg"}
Response: {"data": {"upload_url": "URL_2", "public_url": "PUBLIC_URL_2", ...}}
```

### **3. Upload first image**
```
PUT URL_1
Body: [image1 bytes]
Response: 200 OK
```

### **4. Upload second image**
```
PUT URL_2
Body: [image2 bytes]
Response: 200 OK
```

### **5. Create post**
```
POST /api/posts/
Body: {
  "category": "PROBLEM",
  "description": "...",
  "image_urls": ["PUBLIC_URL_1", "PUBLIC_URL_2"]
}
Response: 201 Created
```

---

## Error Responses

### **Step 1 Errors (Get Upload URL)**

**400 - Missing filename:**
```json
{
  "status": 400,
  "message": "Filename is required"
}
```

**500 - Supabase error:**
```json
{
  "status": 500,
  "message": "Failed to generate upload URL",
  "error": "Error details..."
}
```

---

### **Step 2 Errors (Upload to Supabase)**

**403 - Expired URL:**
```
Upload URL expired (valid for 1 hour only)
```

**413 - File too large:**
```
File size exceeds limit
```

---

### **Step 3 Errors (Create Post)**

**400 - Validation error:**
```json
{
  "status": 400,
  "message": "Failed to create post",
  "errors": {
    "image_urls": [
      "At least one image is required for PROBLEM category."
    ]
  }
}
```

**415 - Wrong Content-Type:**
```json
{
  "detail": "Unsupported media type \"multipart/form-data\" in request."
}
```
**Fix:** Send `Content-Type: application/json`

---

## Field Specifications

### **Post Categories**

| Category | Requires Images | Requires Headline |
|----------|----------------|-------------------|
| `NEWS` | No | Recommended |
| `UPDATE` | No | Recommended |
| `PROBLEM` | **Yes** (at least 1) | Optional |
| `ADVERTISEMENT` | No | No |

### **Image Limits**

- **Max images per post:** 10
- **Supported formats:** JPG, PNG, WebP, etc.
- **Upload URL expires:** 1 hour

---

## Update Post with Images

**Endpoint:** `PUT /api/posts/{post_id}/`

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "category": "PROBLEM",
  "headline": "Updated headline",
  "description": "Updated description",
  "image_urls": [
    "https://new-image-url-1.jpg",
    "https://new-image-url-2.jpg"
  ]
}
```

**Notes:**
- Providing `image_urls` **replaces ALL existing images**
- Omit `image_urls` to keep existing images unchanged
- Follow same 3-step process to upload new images first

**Response (200):**
```json
{
  "status": 200,
  "data": {
    "id": "post-uuid",
    "imageUrls": [
      "https://new-image-url-1.jpg",
      "https://new-image-url-2.jpg"
    ],
    ...
  }
}
```

---

## Important Notes

### ✅ **DO:**
- Send `Content-Type: application/json` for all backend calls
- Upload images to Supabase first, then create post
- Save `public_url` from Step 1 for Step 3
- Handle upload URL expiration (1 hour)

### ❌ **DON'T:**
- Don't send multipart/form-data to `/api/posts/`
- Don't upload images directly to backend
- Don't reuse expired upload URLs
- Don't include more than 10 images

---

## Common Issues

### **Getting 415 Error?**
- Check you're sending `Content-Type: application/json`
- Make sure you're sending JSON body, not form-data

### **Image not appearing?**
- Verify you saved `public_url` (not `upload_url`)
- Check image was successfully uploaded to Supabase (Step 2)
- Confirm `image_urls` array contains valid URLs

### **Upload URL expired?**
- URLs expire after 1 hour
- Generate new URL if needed
- Upload immediately after getting URL

---

## Quick Reference

```
Flow:
1. POST /api/storage/upload-url → get upload_url & public_url
2. PUT upload_url (to Supabase) → upload image bytes
3. POST /api/posts/ → create post with public_url(s)

Headers:
- Backend calls: Content-Type: application/json
- Supabase upload: Content-Type: image/jpeg (or image/png)

Max images: 10
URL expires: 1 hour
Required for: PROBLEM category
```
