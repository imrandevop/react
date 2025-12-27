# Multiple Images Upload Fix

## Issue
When posting multiple images, only one image was being saved to the database.

## Root Cause
The `PostViewSet` was missing the required parser classes (`MultiPartParser`, `FormParser`) to properly handle multipart file uploads with multiple files.

## Fixes Applied

### 1. Added Parser Classes to PostViewSet
**File**: `basic/views.py`

```python
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # ✅ ADDED
```

**What this fixes**:
- `MultiPartParser`: Handles file uploads (including multiple files)
- `FormParser`: Handles standard form data
- `JSONParser`: Handles JSON payloads (for image_urls method)

### 2. Fixed process_image() Function
**File**: `basic/serializers.py`

**Before** (Bug):
```python
sys.getsizeof(output)  # ❌ Returns BytesIO object size, not file size
```

**After** (Fixed):
```python
file_size = len(output.getvalue())  # ✅ Correct file size
```

**Additional improvements**:
- Added try-catch for better error messages
- Fixed filename handling for files with multiple dots
- Changed from `split('.')` to `rsplit('.', 1)`

### 3. Added Transaction Safety
**File**: `basic/serializers.py`

- Wrapped `create()` and `update()` methods in `transaction.atomic()`
- Prevents partial saves if one image fails
- In `update()`, processes all new images before deleting old ones

### 4. Added Image Limits
**File**: `basic/serializers.py`

```python
images = serializers.ListField(
    child=serializers.ImageField(...),
    max_length=10  # ✅ Maximum 10 images per post
)
image_urls = serializers.ListField(
    child=serializers.URLField(),
    max_length=10  # ✅ Maximum 10 images per post
)
```

### 5. Better Error Messages
Now provides specific error messages:
- Which image number failed processing
- What the error was
- Preserves the original filename in error messages

## How to Upload Multiple Images

### Method 1: File Upload (Multipart Form-Data)

```bash
curl -X POST http://localhost:8000/api/posts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "category=PROBLEM" \
  -F "headline=Test Post" \
  -F "description=Test description" \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.jpg" \
  -F "images=@/path/to/image3.jpg"
```

**Important**: Use the same field name `images` multiple times, NOT `images[0]`, `images[1]`, etc.

### Method 2: Supabase URL Upload (JSON)

```bash
curl -X POST http://localhost:8000/api/posts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "PROBLEM",
    "headline": "Test Post",
    "description": "Test description",
    "image_urls": [
      "https://your-supabase-url.com/image1.jpg",
      "https://your-supabase-url.com/image2.jpg",
      "https://your-supabase-url.com/image3.jpg"
    ]
  }'
```

### Method 3: Mixed (File + URL) - NOT RECOMMENDED
While technically supported, it's better to use one method consistently.

## Frontend Implementation Guide

### JavaScript/Fetch Example

```javascript
// Method 1: File Upload
const formData = new FormData();
formData.append('category', 'PROBLEM');
formData.append('headline', 'Test Post');
formData.append('description', 'Test description');

// Add multiple files with the SAME field name
imageFiles.forEach(file => {
  formData.append('images', file);  // Same name for all files
});

const response = await fetch('http://localhost:8000/api/posts/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    // DON'T set Content-Type header - browser will set it automatically
  },
  body: formData
});
```

### React Example

```javascript
const handleSubmit = async (files) => {
  const formData = new FormData();
  formData.append('category', 'PROBLEM');
  formData.append('headline', 'Test Post');
  formData.append('description', 'Test description');

  // Add all selected files
  Array.from(files).forEach(file => {
    formData.append('images', file);
  });

  try {
    const response = await fetch('http://localhost:8000/api/posts/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData
    });

    if (response.ok) {
      const data = await response.json();
      console.log('Post created:', data);
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

### Axios Example

```javascript
import axios from 'axios';

const uploadImages = async (files) => {
  const formData = new FormData();
  formData.append('category', 'PROBLEM');
  formData.append('headline', 'Test Post');
  formData.append('description', 'Test description');

  files.forEach(file => {
    formData.append('images', file);
  });

  try {
    const response = await axios.post(
      'http://localhost:8000/api/posts/',
      formData,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    console.log('Success:', response.data);
  } catch (error) {
    console.error('Error:', error.response?.data);
  }
};
```

## Testing

Run the test script:

```bash
python3 test_multiple_images.py
```

This will:
1. Login and get a token
2. Generate 3 Supabase upload URLs
3. Create a post with 3 image URLs
4. Verify all images are saved

## Common Errors and Solutions

### Error: "Only one image is saved"
**Cause**: Missing parser classes
**Solution**: ✅ Already fixed in this update

### Error: "Error processing image"
**Cause**: Corrupted or invalid image file
**Solution**: Check the error message - it now tells you which image failed and why

### Error: "413 Payload Too Large"
**Cause**: Images are too large
**Solution**:
- Images are automatically resized to max 1080x1080
- Check your nginx/server upload limits
- Reduce quality or use Supabase upload method

### Error: "At least one image is required"
**Cause**: PROBLEM category posts require images
**Solution**: Either provide images or change category to NEWS/UPDATE

## Limits

- **Maximum images per post**: 10
- **Maximum file size**: 10MB per image (set in serializer)
- **Supported formats**: All formats supported by PIL (converted to JPEG)
- **Output format**: All images converted to JPEG at 85% quality
- **Maximum dimensions**: 1080x1080 (automatically resized)

## Database Schema

Each image is stored as a separate `PostImage` record:

```
PostImage {
  id: UUID
  post: ForeignKey(Post)
  image: ImageField (nullable)          # For file uploads
  image_url: URLField (nullable)        # For Supabase URLs
  created_at: DateTime
}
```

Use `get_image_url()` method to get the correct URL regardless of storage method.
