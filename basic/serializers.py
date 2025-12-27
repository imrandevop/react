from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Post, PostImage, PostCategory, Vote, Comment, PostReport
from django.db import transaction

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    localBody = serializers.CharField(required=True)
    pincode = serializers.CharField(required=True)
    userId = serializers.UUIDField(required=True)

    def validate(self, attrs):
        localBody = attrs.get('localBody', '').strip()
        pincode = attrs.get('pincode', '').strip()
        userId = attrs.get('userId')

        if not localBody or not pincode or not userId:
            raise serializers.ValidationError("localBody, pincode, and userId are required.")

        # Check if user exists by userId
        try:
            user = User.objects.get(userId=userId)
            # Update localBody and pincode (user can change locality)
            user.localBody = localBody
            user.pincode = pincode
            user.save()
        except User.DoesNotExist:
            # Create new user with the provided userId
            user = User.objects.create(userId=userId, localBody=localBody, pincode=pincode)
            user.set_unusable_password()
            user.save()

        attrs['user'] = user
        return attrs

    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['image']

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    userId = serializers.CharField(source='user.id', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'userId', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'userId', 'created_at']

    def get_user(self, obj):
        return obj.user.localBody

    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Comment text cannot be empty.")
        return value.strip()

class PostReportSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    userId = serializers.CharField(source='user.id', read_only=True)

    class Meta:
        model = PostReport
        fields = ['id', 'user', 'userId', 'description', 'status', 'created_at']
        read_only_fields = ['id', 'user', 'userId', 'status', 'created_at']

    def get_user(self, obj):
        return obj.user.localBody

    def validate_description(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Report description cannot be empty.")
        return value.strip()

class PostSerializer(serializers.ModelSerializer):
    imageUrls = serializers.SerializerMethodField()
    upvotes = serializers.SerializerMethodField()
    downvotes = serializers.SerializerMethodField()
    commentsCount = serializers.SerializerMethodField()
    hasUpvoted = serializers.SerializerMethodField()
    hasDownvoted = serializers.SerializerMethodField()
    userId = serializers.CharField(source='user.id', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'userId', 'headline', 'imageUrls', 'description',
            'category', 'upvotes', 'downvotes', 'commentsCount',
            'created_at', 'hasUpvoted', 'hasDownvoted'
        ]

    def get_imageUrls(self, obj):
        """Return 1000px WebP transformed URLs for full post view"""
        urls = []
        for img in obj.images.all():
            # Use transformed URL (1000px, WebP, quality 80)
            img_url = img.get_full_url()
            if img_url:
                urls.append(img_url)
        return urls

    def get_upvotes(self, obj):
        return obj.votes.filter(vote_type=Vote.UPVOTE).count()

    def get_downvotes(self, obj):
        return obj.votes.filter(vote_type=Vote.DOWNVOTE).count()

    def get_commentsCount(self, obj):
        return obj.comments.count()

    def get_hasUpvoted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.votes.filter(user=request.user, vote_type=Vote.UPVOTE).exists()
        return False

    def get_hasDownvoted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.votes.filter(user=request.user, vote_type=Vote.DOWNVOTE).exists()
        return False

class PostCreateUpdateSerializer(serializers.ModelSerializer):
    # Supabase URL-based upload only
    image_urls = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False,
        max_length=10  # Maximum 10 images per post
    )
    headline = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Post
        fields = ['category', 'headline', 'description', 'image_urls']

    def validate(self, attrs):
        category = attrs.get('category')
        image_urls = attrs.get('image_urls', [])

        if self.instance is None:  # Create
            # For PROBLEM category, require at least one image URL
            if category == PostCategory.PROBLEM and not image_urls:
                raise serializers.ValidationError({
                    "image_urls": "At least one image is required for PROBLEM category."
                })

        return attrs

    def create(self, validated_data):
        image_urls_data = validated_data.pop('image_urls', [])
        user = self.context['request'].user
        pincode = user.pincode

        # Use transaction to ensure all-or-nothing creation
        with transaction.atomic():
            post = Post.objects.create(user=user, pincode=pincode, **validated_data)

            # Create PostImage records for each Supabase URL
            for image_url in image_urls_data:
                PostImage.objects.create(post=post, image_url=image_url)

        return post

    def update(self, instance, validated_data):
        image_urls_data = validated_data.pop('image_urls', None)

        # Use transaction to ensure all-or-nothing update
        with transaction.atomic():
            instance.headline = validated_data.get('headline', instance.headline)
            instance.description = validated_data.get('description', instance.description)
            instance.save()

            # If image_urls is provided, replace all images
            if image_urls_data is not None:
                # Delete old images
                instance.images.all().delete()

                # Create new image records from Supabase URLs
                for image_url in image_urls_data:
                    PostImage.objects.create(post=instance, image_url=image_url)

        return instance

class AdSerializer(serializers.ModelSerializer):
    imageUrls = serializers.SerializerMethodField()
    title = serializers.CharField(source='headline')
    sponsorName = serializers.CharField(source='sponsor_name')
    buttonText = serializers.CharField(source='button_text')
    buttonUrl = serializers.CharField(source='button_url')

    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'imageUrls', 'buttonText', 'buttonUrl', 'sponsorName']

    def get_imageUrls(self, obj):
        request = self.context.get('request')
        urls = []
        for img in obj.images.all():
            # Use the model's get_image_url method which handles both Supabase URLs and local files
            img_url = img.get_image_url(request)
            if img_url:
                urls.append(img_url)
        return urls

class FeedPostSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for feed listing
    Returns only: id, headline, image_thumb_url, created_at
    """
    image_thumb_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'headline', 'image_thumb_url', 'created_at']

    def get_image_thumb_url(self, obj):
        """Return 400px WebP thumbnail URL"""
        first_image = obj.images.first()
        if first_image:
            return first_image.get_thumbnail_url()
        return None
