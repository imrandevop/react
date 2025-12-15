from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import PostImage
import os

@receiver(post_delete, sender=PostImage)
def delete_post_image_file(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
