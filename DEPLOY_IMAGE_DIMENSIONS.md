# Deploy Image Dimensions Feature

## Changes Made
- Added `width` and `height` fields to `PostImage` model
- API now returns `imageDimensions` array alongside `imageUrls`
- Dimensions are fetched automatically during post creation
- Old images return `null` for dimensions

## Example API Response
```json
{
  "id": 123,
  "imageUrls": [
    "https://.../image1.jpg",
    "https://.../image2.jpg"
  ],
  "imageDimensions": [
    {"width": 1080, "height": 1350},
    {"width": 1920, "height": 1080}
  ],
  ...
}
```

## Deployment Steps

### 1. Push Code
```bash
git add .
git commit -m "Add image dimensions feature"
git push origin main
```

### 2. On Production Server
```bash
cd /var/www/react/react
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt

# Run migration
python manage.py migrate

# Clear cache
python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared')"

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### 3. Test
Create a new post with images - it should automatically include dimensions.

Old posts will show `null` for dimensions (as expected).

## Notes
- Post creation will be slightly slower (1-2 seconds) as it fetches image dimensions
- This is acceptable trade-off for better Flutter performance
- Flutter can now pre-calculate aspect ratios and avoid layout shifts
