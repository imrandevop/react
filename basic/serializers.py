from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    localBody = serializers.CharField(required=True, min_length=1)
    pincode = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate(self, attrs):
        localBody = attrs.get('localBody')
        pincode = attrs.get('pincode')

        try:
            user = User.objects.get(localBody=localBody)
        except User.DoesNotExist:
             raise serializers.ValidationError({"localBody": "User not found."})

        # Plain text comparison as requested
        if user.pincode != pincode:
            raise serializers.ValidationError({"pincode": "Invalid pincode."})
        
        attrs['user'] = user
        return attrs

    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
