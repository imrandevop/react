from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Post, PostImage, PostCategory, Vote
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    localBody = serializers.CharField(required=True)
    pincode = serializers.CharField(required=True)

    def validate(self, attrs):
        localBody = attrs.get('localBody', '').strip()
        pincode = attrs.get('pincode', '').strip()

        if not localBody or not pincode:
            raise serializers.ValidationError("Both localBody and pincode are required.")

        # Check if user exists (case-insensitive)
        try:
            user = User.objects.get(localBody__iexact=localBody)
            # Option A: Update pincode to match the latest login attempt
            user.pincode = pincode
            user.save()
        except User.DoesNotExist:
            # Auto-create user if not found
            user = User.objects.create(localBody=localBody, pincode=pincode)
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

def process_image(image):
    im = Image.open(image)
    if im.mode != 'RGB':
        im = im.convert('RGB')
    
    im.thumbnail((1080, 1080))
    
    output = BytesIO()
    im.save(output, format='JPEG', quality=85)
    output.seek(0)
    
    return InMemoryUploadedFile(
        output,
        'ImageField',
        "%s.jpg" % image.name.split('.')[0],
        'image/jpeg',
        sys.getsizeof(output),
        None
    )

class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['image']

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
        request = self.context.get('request')
        urls = []
        for img in obj.images.all():
            if request:
                urls.append(request.build_absolute_uri(img.image.url))
            else:
                urls.append(img.image.url)
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
    images = serializers.ListField(
        child=serializers.ImageField(max_length=10000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    headline = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Post
        fields = ['category', 'headline', 'description', 'images']

    def validate(self, attrs):
        category = attrs.get('category')
        images = attrs.get('images', [])

        if self.instance is None: # Create
            if category == PostCategory.PROBLEM and not images:
                raise serializers.ValidationError({"images": "At least one image is required for PROBLEM category."})
        
        return attrs

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        user = self.context['request'].user
        pincode = user.pincode
        
        post = Post.objects.create(user=user, pincode=pincode, **validated_data)
        
        for image_data in images_data:
            processed_image = process_image(image_data)
            PostImage.objects.create(post=post, image=processed_image)
            
        return post

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)
        
        instance.headline = validated_data.get('headline', instance.headline)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        if images_data is not None:
            # Replace images fully
            instance.images.all().delete()
            for image_data in images_data:
                processed_image = process_image(image_data)
                PostImage.objects.create(post=instance, image=processed_image)
        
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
             if request:
                urls.append(request.build_absolute_uri(img.image.url))
             else:
                urls.append(img.image.url)
        return urls
