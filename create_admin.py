 #!/usr/bin/env python
"""
Script to create an admin user for the Django admin panel.
Run this with: python manage.py shell < create_admin.py
"""
import uuid
from basic.models import User

# Configuration - Modify these values
LOCAL_BODY = "Admin User"
PINCODE = "000000"

# Create admin user with a UUID
try:
    # Generate a UUID for the admin
    admin_uuid = uuid.uuid4()

    # Check if admin already exists
    if User.objects.filter(is_admin=True).exists():
        admin = User.objects.filter(is_admin=True).first()
        print(f"Admin user already exists!")
        print(f"UUID: {admin.userId}")
        print(f"Local Body: {admin.localBody}")
        print(f"Pincode: {admin.pincode}")
    else:
        # Create new admin user
        admin = User.objects.create_superuser(
            userId=admin_uuid,
            localBody=LOCAL_BODY,
            pincode=PINCODE
        )
        print(f"Admin user created successfully!")
        print(f"UUID: {admin.userId}")
        print(f"Local Body: {admin.localBody}")
        print(f"Pincode: {admin.pincode}")

    print(f"\nTo login to admin panel, use:")
    print(f"Username: {admin.userId}")
    print(f"Password: (leave blank or use pincode: {admin.pincode})")

except Exception as e:
    print(f"Error creating admin user: {e}")
