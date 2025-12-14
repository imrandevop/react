from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = serializer.get_token(user)
            
            return Response({
                "status": 200,
                "data": {
                    "token": tokens['access'],
                    "user": {
                        "id": str(user.id),
                        "localBody": user.localBody,
                        "pincode": user.pincode
                    }
                }
            }, status=status.HTTP_200_OK)
        
        # Error formatting
        return Response({
            "status": 400,
            "data": {
                "message": "Login Failed",
                "errors": serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
