from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, localBody, pincode=None):
        if not localBody:
            raise ValueError('Users must have a localBody')
        user = self.model(localBody=localBody, pincode=pincode)
        # Storing pincode as plain text as requested.
        # We are NOT hashing it into the 'password' field.
        user.set_unusable_password() 
        user.save(using=self._db)
        return user

    def create_superuser(self, localBody, pincode=None):
        user = self.create_user(localBody, pincode=pincode)
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    localBody = models.CharField(max_length=255, unique=True)
    pincode = models.CharField(max_length=6)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'localBody'
    REQUIRED_FIELDS = ['pincode']

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
    
    # Ad specific fields
    sponsor_name = models.CharField(max_length=255, null=True, blank=True)
    button_text = models.CharField(max_length=50, null=True, blank=True)
    button_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.localBody} - {self.category} - {self.id}"

class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='post_images/')

    def __str__(self):
        return f"Image for Post {self.post.id}"

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
