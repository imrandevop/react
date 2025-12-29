"""
Utility functions for image processing
"""
import requests
from PIL import Image
from io import BytesIO


def get_image_dimensions_from_url(url: str) -> tuple:
    """
    Fetch image from URL and return dimensions (width, height)

    Args:
        url: Image URL to fetch

    Returns:
        Tuple of (width, height) or (None, None) if error
    """
    try:
        # Download image with timeout
        response = requests.get(url, timeout=10, stream=True)
        response.raise_for_status()

        # Open image and get dimensions
        img = Image.open(BytesIO(response.content))
        width, height = img.size

        return width, height
    except Exception as e:
        print(f"Error fetching image dimensions from {url}: {str(e)}")
        return None, None
