from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import uuid

class UserManager(BaseUserManager):
    def create_user(self, username=None, userId=None, localBody=None, pincode=None, password=None):
        # For regular API users (no username, no password)
        if not username:
            if not userId:
                userId = uuid.uuid4()
            if not localBody:
                raise ValueError('Users must have a localBody')
            user = self.model(userId=userId, localBody=localBody, pincode=pincode, username=None)
            user.set_unusable_password()
            user.save(using=self._db)
            return user

        # For admin users (with username and password)
        if not localBody:
            localBody = username  # Use username as localBody for admin
        user = self.model(username=username, userId=userId or uuid.uuid4(), localBody=localBody, pincode=pincode or '000000')
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        localBody = extra_fields.get('localBody', username)
        pincode = extra_fields.get('pincode', '000000')

        user = self.model(
            username=username,
            userId=uuid.uuid4(),
            localBody=localBody,
            pincode=pincode,
            is_admin=True,
            is_active=True
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    userId = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    localBody = models.CharField(max_length=255)
    pincode = models.CharField(max_length=6)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)  # For admin login only
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['localBody', 'pincode']

    def __str__(self):
        return self.localBody

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

class PostCategory(models.TextChoices):
    NEWS = "NEWS", "News"
    UPDATE = "UPDATE", "Update"
    PROBLEM = "PROBLEM", "Problem"
    ADVERTISEMENT = "ADVERTISEMENT", "Advertisement"

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.CharField(max_length=20, choices=PostCategory.choices)
    headline = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    pincode = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_ad_approved = models.BooleanField(default=False)

    # Hot score for Reddit-style ranking (higher = better)
    hot_score = models.FloatField(default=0.0, db_index=True)

    # Ad specific fields
    sponsor_name = models.CharField(max_length=255, null=True, blank=True)
    button_text = models.CharField(max_length=50, null=True, blank=True)
    button_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.localBody} - {self.category} - {self.id}"

    def calculate_hot_score(self):
        """
        Calculate Reddit-style hot score
        Combines upvotes/downvotes with time decay
        """
        from django.utils import timezone
        import math
        from datetime import datetime

        # Get vote counts
        upvotes = self.votes.filter(vote_type=Vote.UPVOTE).count()
        downvotes = self.votes.filter(vote_type=Vote.DOWNVOTE).count()
        score = upvotes - downvotes

        # Reddit's hot algorithm
        order = math.log10(max(abs(score), 1))

        if score > 0:
            sign = 1
        elif score < 0:
            sign = -1
        else:
            sign = 0

        # Epoch time: seconds since a reference point
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        seconds = (self.created_at - epoch).total_seconds() - 1134028003

        # Calculate and return hot score
        return round(sign * order + seconds / 45000, 7)

    def update_hot_score(self):
        """Update and save the hot score"""
        self.hot_score = self.calculate_hot_score()
        self.save(update_fields=['hot_score'])

class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    # Support both local file uploads (backward compatibility) and Supabase URLs
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    # Image dimensions for aspect ratio calculation
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Image for Post {self.post.id}"
    
    def get_image_url(self, request=None):
        """Get the image URL - either from Supabase or local media"""
        if self.image_url:
            # Strip whitespace, newlines, and trailing ? characters
            return self.image_url.strip().rstrip('?')
        elif self.image:
            if request:
                return request.build_absolute_uri(self.image.url)
            return self.image.url
        return None

    def get_transformed_url(self, width=1000, quality=80, request=None):
        """
        Get image URL (Supabase transformation disabled, returns direct URL)

        Note: Supabase Image Transformation API is not enabled for this project.
        Returns direct object URLs instead. Flutter/frontend should handle image
        optimization via caching and lazy loading.

        Args:
            width: Ignored (kept for API compatibility)
            quality: Ignored (kept for API compatibility)
            request: Django request object for building absolute URIs

        Returns:
            Direct Supabase Storage URL or original URL
        """
        base_url = self.get_image_url(request=request)
        if not base_url:
            return None

        # Return direct URL (transformation not available)
        return base_url

    def get_thumbnail_url(self, request=None):
        """Get 400px thumbnail URL with WebP format"""
        return self.get_transformed_url(width=400, quality=80, request=request)

    def get_full_url(self, request=None):
        """Get 1000px full-size URL with WebP format"""
        return self.get_transformed_url(width=1000, quality=80, request=request)

class Vote(models.Model):
    UPVOTE = 1
    DOWNVOTE = -1
    VOTE_CHOICES = (
        (UPVOTE, 'Upvote'),
        (DOWNVOTE, 'Downvote'),
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.IntegerField(choices=VOTE_CHOICES)

    class Meta:
        unique_together = ('post', 'user')

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class ReportStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    REVIEWED = "REVIEWED", "Reviewed"
    RESOLVED = "RESOLVED", "Resolved"

class PostReport(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"Report by {self.user.localBody} on Post {self.post.id}"

class UserBlock(models.Model):
    """
    One-way user blocking system
    blocker: The user who is blocking
    blocked: The user who is being blocked
    """
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocking')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.blocker.localBody} blocked {self.blocked.localBody}"

    def save(self, *args, **kwargs):
        if self.blocker == self.blocked:
            raise ValueError("Users cannot block themselves")
        super().save(*args, **kwargs)
