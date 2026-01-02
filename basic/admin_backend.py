"""
Custom authentication backend for Django admin panel.
Allows normal username/password authentication for admin users.
API users (without username) are not affected.
"""
from django.contrib.auth.backends import ModelBackend


class AdminBackend(ModelBackend):
    """
    Standard Django authentication backend.
    Works only for users with a username field (admin users).
    Regular API users (username=None) won't be able to login to admin panel.
    """
    pass
