from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginAPIView, PostViewSet, FeedAPIView, DeleteAccountAPIView, GenerateUploadURLAPIView

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')

urlpatterns = [
    path('auth/login', LoginAPIView.as_view(), name='login'),
    path('auth/delete-account', DeleteAccountAPIView.as_view(), name='delete-account'),
    path('feed', FeedAPIView.as_view(), name='feed'),
    path('storage/upload-url', GenerateUploadURLAPIView.as_view(), name='upload-url'),
    path('', include(router.urls)),
]
