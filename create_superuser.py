#!/usr/bin/env python
"""
Script to create a superuser with username/password for Django admin panel.
"""
from basic.models import User

# Configuration - Modify these as needed
USERNAME = "react"
PASSWORD = "react1210"  # Change this to a secure password
LOCAL_BODY = "Admin"
PINCODE = "000000"

try:
    # Check if user already exists
    if User.objects.filter(username=USERNAME).exists():
        user = User.objects.get(username=USERNAME)
        print(f"User '{USERNAME}' already exists!")
        print(f"Username: {user.username}")
        print(f"Is Admin: {user.is_admin}")
    else:
        # Create superuser
        user = User.objects.create_superuser(
            username=USERNAME,
            password=PASSWORD,
            localBody=LOCAL_BODY,
            pincode=PINCODE
        )
        print(f"Superuser created successfully!")
        print(f"Username: {USERNAME}")
        print(f"Password: {PASSWORD}")
        print(f"\nYou can now login to /admin with these credentials")

except Exception as e:
    print(f"Error creating superuser: {e}")
    import traceback
    traceback.print_exc()
