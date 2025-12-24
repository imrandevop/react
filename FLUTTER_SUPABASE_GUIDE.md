# Supabase Storage Integration - Flutter API Documentation

## Overview

The Django backend now supports **direct image uploads to Supabase Storage** using signed URLs. This allows Flutter to upload images directly to Supabase without going through the Django server, improving performance and reducing server load.

## New Upload Flow

```
1. Flutter → Django: Request signed upload URL
   POST /api/storage/upload-url

2. Django → Supabase: Generate signed URL
   (Django calls Supabase Storage API)

3. Django → Flutter: Return signed URL + public URL
   Response contains upload_url and public_url

4. Flutter → Supabase: Upload image directly
   PUT to upload_url with image data

5. Flutter → Django: Create post with public URL
   POST /api/posts/ with image_urls field

6. Django → Database: Save post with image URLs
```

## API Endpoints

### 1. Generate Signed Upload URL

Request a signed URL to upload an image directly to Supabase.

**Endpoint:** `POST /api/storage/upload-url`

**Headers:**
```http
Authorization: Bearer {your_jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "filename": "my-photo.jpg",
  "content_type": "image/jpeg"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "data": {
    "upload_url": "https://fhyorgkvdamjuboftetp.supabase.co/storage/v1/object/upload/react/posts/20251224-abc123.jpg?token=...",
    "file_path": "posts/20251224-abc123.jpg",
    "public_url": "https://fhyorgkvdamjuboftetp.supabase.co/storage/v1/object/public/react/posts/20251224-abc123.jpg",
    "expires_in": 3600
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": 400,
  "message": "filename is required"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 2. Upload Image to Supabase

After receiving the signed URL, upload your image directly to Supabase.

**Endpoint:** Use the `upload_url` from step 1

**Method:** `PUT` (not POST!)

**Headers:**
```http
Content-Type: image/jpeg
```

**Body:** Raw image binary data

**Example (Dart/Flutter):**
```dart
import 'package:http/http.dart' as http;
import 'dart:io';

Future<void> uploadImageToSupabase(String uploadUrl, File imageFile) async {
  final bytes = await imageFile.readAsBytes();
  
  final response = await http.put(
    Uri.parse(uploadUrl),
    headers: {'Content-Type': 'image/jpeg'},
    body: bytes,
  );
  
  if (response.statusCode == 200) {
    print('Image uploaded successfully!');
  } else {
    print('Upload failed: ${response.statusCode}');
    throw Exception('Failed to upload image');
  }
}
```

---

### 3. Create Post with Image URLs

After uploading images to Supabase, create a post using the public URLs.

**Endpoint:** `POST /api/posts/`

**Headers:**
```http
Authorization: Bearer {your_jwt_token}
Content-Type: application/json
```

**Request Body (NEW - with image URLs):**
```json
{
  "category": "NEWS",
  "headline": "Breaking News",
  "description": "This is a test post with Supabase images",
  "image_urls": [
    "https://fhyorgkvdamjuboftetp.supabase.co/storage/v1/object/public/react/posts/20251224-abc123.jpg",
    "https://fhyorgkvdamjuboftetp.supabase.co/storage/v1/object/public/react/posts/20251224-def456.jpg"
  ]
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "data": {
    "id": 22,
    "userId": "10",
    "headline": "Breaking News",
    "imageUrls": [
      "https://fhyorgkvdamjuboftetp.supabase.co/storage/v1/object/public/react/posts/20251224-abc123.jpg",
      "https://fhyorgkvdamjuboftetp.supabase.co/storage/v1/object/public/react/posts/20251224-def456.jpg"
    ],
    "description": "This is a test post with Supabase images",
    "category": "NEWS",
    "upvotes": 0,
    "downvotes": 0,
    "commentsCount": 0,
    "created_at": "2025-12-24T09:32:15.123Z",
    "hasUpvoted": false,
    "hasDownvoted": false
  }
}
```

---

## Complete Flutter Implementation Example

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';

class SupabaseImageUploader {
  final String baseUrl = 'https://your-server.com/api';
  final String authToken;

  SupabaseImageUploader(this.authToken);

  /// Complete flow: Upload image and create post
  Future<Map<String, dynamic>> createPostWithImages({
    required List<File> images,
    required String category,
    required String description,
    String? headline,
  }) async {
    // Step 1: Upload all images to Supabase
    List<String> imageUrls = [];
    
    for (File image in images) {
      try {
        // 1a. Get signed upload URL
        final uploadUrlData = await _getSignedUploadUrl(
          filename: image.path.split('/').last,
        );
        
        // 1b. Upload image to Supabase
        await _uploadToSupabase(
          uploadUrl: uploadUrlData['upload_url'],
          imageFile: image,
        );
        
        // 1c. Store public URL
        imageUrls.add(uploadUrlData['public_url']);
      } catch (e) {
        print('Failed to upload image: $e');
        rethrow;
      }
    }
    
    // Step 2: Create post with image URLs
    return await _createPost(
      category: category,
      description: description,
      headline: headline,
      imageUrls: imageUrls,
    );
  }

  /// Get signed upload URL from Django
  Future<Map<String, dynamic>> _getSignedUploadUrl({
    required String filename,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/storage/upload-url'),
      headers: {
        'Authorization': 'Bearer $authToken',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'filename': filename,
        'content_type': 'image/jpeg',
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['data'];
    } else {
      throw Exception('Failed to get upload URL: ${response.body}');
    }
  }

  /// Upload image to Supabase Storage
  Future<void> _uploadToSupabase({
    required String uploadUrl,
    required File imageFile,
  }) async {
    final bytes = await imageFile.readAsBytes();
    
    final response = await http.put(
      Uri.parse(uploadUrl),
      headers: {'Content-Type': 'image/jpeg'},
      body: bytes,
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to upload to Supabase: ${response.statusCode}');
    }
  }

  /// Create post with image URLs
  Future<Map<String, dynamic>> _createPost({
    required String category,
    required String description,
    String? headline,
    required List<String> imageUrls,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/posts/'),
      headers: {
        'Authorization': 'Bearer $authToken',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'category': category,
        'description': description,
        'headline': headline,
        'image_urls': imageUrls,
      }),
    );

    if (response.statusCode == 201) {
      final data = jsonDecode(response.body);
      return data['data'];
    } else {
      throw Exception('Failed to create post: ${response.body}');
    }
  }
}

// Usage Example:
void main() async {
  final uploader = SupabaseImageUploader('your_jwt_token_here');
  
  final images = [
    File('/path/to/image1.jpg'),
    File('/path/to/image2.jpg'),
  ];
  
  try {
    final post = await uploader.createPostWithImages(
      images: images,
      category: 'NEWS',
      headline: 'My News Post',
      description: 'This is a test post',
    );
    
    print('Post created: ${post['id']}');
  } catch (e) {
    print('Error: $e');
  }
}
```

---

## Image Processing Guidelines

**IMPORTANT:** Flutter must resize/compress images **before upload**, as Django no longer processes images in the new flow.

**Recommended specifications:**
- Max dimensions: 1080x1080 pixels
- Format: JPEG
- Quality: 85%
- Max file size: 2MB

**Flutter Example (using image package):**
```dart
import 'package:image/image.dart' as img;
import 'dart:io';

Future<File> compressImage(File imageFile) async {
  // Read image
  final bytes = await imageFile.readAsBytes();
  final image = img.decodeImage(bytes);
  
  if (image == null) throw Exception('Failed to decode image');
  
  // Resize if needed
  final resized = img.copyResize(
    image,
    width: image.width > 1080 ? 1080 : image.width,
    height: image.height > 1080 ? 1080 : image.height,
  );
  
  // Compress as JPEG
  final compressed = img.encodeJpg(resized, quality: 85);
  
  // Save to temp file
  final tempFile = File('${imageFile.path}_compressed.jpg');
  await tempFile.writeAsBytes(compressed);
  
  return tempFile;
}
```

---

## Backward Compatibility

The backend **still supports the old multipart file upload** method for backward compatibility.

**Old Method (still works):**
```http
POST /api/posts/
Content-Type: multipart/form-data

category=NEWS
headline=Test
description=Test post
images=[binary file data]
```

You can continue using this method if needed, but the new URL-based method is **recommended** for better performance.

---

## Error Handling

### Common Errors

**1. Invalid Token (401)**
```json
{
  "detail": "Given token not valid for any token type"
}
```
→ Refresh your JWT token by logging in again

**2. Missing filename (400)**
```json
{
  "status": 400,
  "message": "filename is required"
}
```
→ Ensure filename is provided in request

**3. Supabase Upload Failed**
- Check if Supabase bucket is public
- Verify Supabase credentials in backend .env file
- Ensure signed URL hasn't expired (valid for 1 hour)

**4. PROBLEM category without images (400)**
```json
{
  "images": ["At least one image is required for PROBLEM category."]
}
```
→ PROBLEM posts require at least one image

---

## Testing Checklist

Before deploying to production:

- [ ] Test image upload to Supabase
- [ ] Verify image URLs are accessible (public bucket)
- [ ] Test post creation with Supabase URLs
- [ ] Verify existing posts with local images still work
- [ ] Test with multiple images
- [ ] Test image size limits
- [ ] Test network error handling
- [ ] Test expired signed URL handling

---

## Configuration

### Supabase Bucket Setup

Ensure your Supabase bucket is configured as **public**:

1. Go to Supabase Dashboard → Storage
2. Select `react` bucket
3. Make bucket public (if not already)
4. Verify bucket policies allow uploads

### Backend Configuration

Verify these environment variables are set in `.env`:

```env
SUPABASE_URL=https://fhyorgkvdamjuboftetp.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
SUPABASE_BUCKET_NAME=react
```

---

## Support

If you encounter any issues:

1. Check Django server logs for detailed error messages
2. Verify Supabase bucket permissions
3. Ensure images are properly compressed before upload
4. Test with Postman/curl first to isolate Flutter-specific issues

---

## Migration Notes

**For existing Flutter code:**

1. Update image upload logic to use new 3-step flow
2. Add image compression before upload
3. Change from multipart/form-data to JSON requests
4. Update post creation to use `image_urls` instead of `images`

**No changes needed for:**
- Authentication
- Feed APIs
- Voting APIs
- Comment APIs
- All other existing endpoints
