from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginAPIView, PostViewSet, FeedAPIView, FeedRefreshAPIView

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')

urlpatterns = [
    path('auth/login', LoginAPIView.as_view(), name='login'),
    path('feed', FeedAPIView.as_view(), name='feed'),
    path('feed/refresh', FeedRefreshAPIView.as_view(), name='feed-refresh'),
    path('', include(router.urls)),
]
