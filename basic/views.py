from rest_framework.views import APIView
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.parsers import JSONParser
from django.db.models import Count, Q
from django.utils import timezone
from .models import Post, PostCategory, Vote, Comment, PostReport
from .serializers import LoginSerializer, PostSerializer, PostCreateUpdateSerializer, AdSerializer, CommentSerializer, PostReportSerializer

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
                        "userId": str(user.userId),
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

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100

class FeedNewestCursorPagination(CursorPagination):
    """Instagram-style: Newest first"""
    page_size = 20
    ordering = '-created_at'
    cursor_query_param = 'cursor'
    page_size_query_param = 'limit'
    max_page_size = 100

class FeedHotCursorPagination(CursorPagination):
    """Reddit-style: Hot score (for Today tab only)"""
    page_size = 20
    ordering = '-hot_score'
    cursor_query_param = 'cursor'
    page_size_query_param = 'limit'
    max_page_size = 100

class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    parser_classes = [JSONParser]  # Only JSON for Supabase URLs
    
    def get_queryset(self):
        user = self.request.user
        # Allow voting and viewing any post, not just from user's pincode
        if self.action in ['retrieve', 'upvote', 'downvote', 'comments', 'update_comment', 'delete_comment', 'report']:
            return Post.objects.all()
        # For listing and other actions, filter by pincode
        queryset = Post.objects.filter(pincode=user.pincode)
        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateUpdateSerializer
        return PostSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
             return Response({
                "status": 400,
                "message": "Failed to create post",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)

        # Calculate initial hot score for new post
        serializer.instance.update_hot_score()

        read_serializer = PostSerializer(serializer.instance, context={'request': request})
        return Response({
            "status": 201,
            "data": read_serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if instance.user != request.user and not request.user.is_admin:
             return Response({"status": 403, "message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        if not serializer.is_valid():
             return Response({
                "status": 400,
                "message": "Failed to update post",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        self.perform_update(serializer)
        
        read_serializer = PostSerializer(instance, context={'request': request})
        return Response({
            "status": 200,
            "data": read_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user and not request.user.is_admin:
             return Response({"status": 403, "message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
             
        self.perform_destroy(instance)
        return Response({
            "status": 200,
            "message": "Post deleted successfully"
        })

    def list(self, request, *args, **kwargs):
        # NOTE: This default list method is only for generic access if needed.
        # The main feed access is via /api/feed. However, consistent with previous steps,
        # we can keep basic filtering here or redirect logic.
        # For this step, I will leave standard listing behavior but 
        # the user requested specific /api/feed endpoint logic.
        # The prompt implies specialized logic for tabs.
        
        queryset = self.filter_queryset(self.get_queryset())

        # Apply basic filtering if used as a backup
        filter_param = self.request.query_params.get('filter')
        if filter_param == 'TODAY':
            now = timezone.now()
            queryset = queryset.filter(created_at__date=now.date()).order_by('-hot_score', '-created_at')
        elif filter_param == 'PROBLEMS':
            queryset = queryset.filter(category=PostCategory.PROBLEM).order_by('-created_at')
        elif filter_param == 'UPDATES':
            queryset = queryset.filter(category=PostCategory.UPDATE).order_by('-created_at')
        elif filter_param == 'YOURS':
            queryset = queryset.filter(user=request.user).order_by('-created_at')
        else:
            # Default: Instagram-style newest first
            queryset = queryset.order_by('-created_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": 200,
            "data": serializer.data
        })

    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        post = self.get_object()
        user = request.user

        try:
            vote = Vote.objects.get(post=post, user=user)
            if vote.vote_type == Vote.UPVOTE:
                vote.delete() # Remove upvote
            else:
                vote.vote_type = Vote.UPVOTE # Change to upvote
                vote.save()
        except Vote.DoesNotExist:
            Vote.objects.create(post=post, user=user, vote_type=Vote.UPVOTE)

        # Update hot score after vote change
        post.update_hot_score()

        return self._vote_response(post, user)

    @action(detail=True, methods=['post'])
    def downvote(self, request, pk=None):
        post = self.get_object()
        user = request.user

        try:
            vote = Vote.objects.get(post=post, user=user)
            if vote.vote_type == Vote.DOWNVOTE:
                vote.delete() # Remove downvote
            else:
                vote.vote_type = Vote.DOWNVOTE # Change to downvote
                vote.save()
        except Vote.DoesNotExist:
            Vote.objects.create(post=post, user=user, vote_type=Vote.DOWNVOTE)

        # Update hot score after vote change
        post.update_hot_score()

        return self._vote_response(post, user)

    def _vote_response(self, post, user):
        upvotes = post.votes.filter(vote_type=Vote.UPVOTE).count()
        downvotes = post.votes.filter(vote_type=Vote.DOWNVOTE).count()
        has_upvoted = post.votes.filter(user=user, vote_type=Vote.UPVOTE).exists()
        has_downvoted = post.votes.filter(user=user, vote_type=Vote.DOWNVOTE).exists()

        return Response({
            "status": 200,
            "data": {
                "upvotes": upvotes,
                "downvotes": downvotes,
                "hasUpvoted": has_upvoted,
                "hasDownvoted": has_downvoted
            }
        })

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        post = self.get_object()

        if request.method == 'GET':
            # List all comments for this post, ordered oldest first
            comments = post.comments.all().order_by('created_at')
            serializer = CommentSerializer(comments, many=True, context={'request': request})
            return Response({
                "status": 200,
                "data": serializer.data
            })

        elif request.method == 'POST':
            # Create a new comment
            serializer = CommentSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(post=post, user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'], url_path='update_comment')
    def update_comment(self, request, pk=None):
        post = self.get_object()
        comment_id = request.data.get('comment_id')

        if not comment_id:
            return Response(
                {"error": "comment_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            comment = Comment.objects.get(id=comment_id, post=post)
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permission: only comment author can edit
        if comment.user != request.user:
            return Response(
                {"error": "You can only edit your own comments"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CommentSerializer(comment, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='delete_comment')
    def delete_comment(self, request, pk=None):
        post = self.get_object()
        comment_id = request.data.get('comment_id') or request.query_params.get('comment_id')

        if not comment_id:
            return Response(
                {"error": "comment_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            comment = Comment.objects.get(id=comment_id, post=post)
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permission: only comment author can delete
        if comment.user != request.user:
            return Response(
                {"error": "You can only delete your own comments"},
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()
        return Response(
            {"message": "Comment deleted successfully"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        post = self.get_object()
        user = request.user

        # Check if user has already reported this post
        if PostReport.objects.filter(post=post, user=user).exists():
            return Response({
                "status": 400,
                "message": "You have already reported this post"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create the report
        serializer = PostReportSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(post=post, user=user)

            # Get total report count for this post
            report_count = post.reports.count()

            return Response({
                "status": 201,
                "data": {
                    "message": "Post reported successfully",
                    "report": serializer.data,
                    "total_reports": report_count
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": 400,
            "message": "Failed to report post",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class FeedAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tab = request.query_params.get('tab')
        if not tab:
             return Response({"status": 400, "message": "Tab parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        valid_tabs = ["All", "Today", "Problems", "Updates", "Yours"]
        # Case insensitive check matching
        tab_mapped = next((t for t in valid_tabs if t.lower() == tab.lower()), None)

        if not tab_mapped:
             return Response({"status": 400, "message": "Invalid feed tab"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Base Filter: Locality/Pincode with Priority
        # Priority: pincode > localBody > user's pincode
        pincode_param = request.query_params.get('pincode')
        localbody_param = request.query_params.get('localBody')

        if pincode_param:
            # Highest priority: filter by pincode parameter
            queryset = Post.objects.filter(pincode=pincode_param)
        elif localbody_param:
            # Second priority: filter by localBody parameter (through user relationship)
            queryset = Post.objects.filter(user__localBody=localbody_param)
        else:
            # Default: filter by user's pincode
            queryset = Post.objects.filter(pincode=user.pincode)
        
        # Filter out ADVERTISEMENTS from main post stream (as discussed)
        queryset = queryset.exclude(category=PostCategory.ADVERTISEMENT)

        # Tab Logic
        # "Today" tab: Reddit-style hot score (upvotes + time decay)
        # All other tabs: Instagram-style newest first

        if tab_mapped == "All":
            queryset = queryset.order_by('-created_at')
            paginator = FeedNewestCursorPagination()

        elif tab_mapped == "Today":
            now = timezone.now()
            queryset = queryset.filter(created_at__date=now.date()).order_by('-hot_score', '-created_at')
            paginator = FeedHotCursorPagination()

        elif tab_mapped == "Problems":
            queryset = queryset.filter(category=PostCategory.PROBLEM).order_by('-created_at')
            paginator = FeedNewestCursorPagination()

        elif tab_mapped == "Updates":
            queryset = queryset.filter(category=PostCategory.UPDATE).order_by('-created_at')
            paginator = FeedNewestCursorPagination()

        elif tab_mapped == "Yours":
            queryset = queryset.filter(user=user).order_by('-created_at')
            paginator = FeedNewestCursorPagination()

        # Cursor-based Pagination
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            post_serializer = PostSerializer(page, many=True, context={'request': request})

            # Ads Retrieval (Separate List)
            # Use same locality filter as posts for ads
            if pincode_param:
                ads_queryset = Post.objects.filter(pincode=pincode_param, category=PostCategory.ADVERTISEMENT, is_ad_approved=True)
            elif localbody_param:
                ads_queryset = Post.objects.filter(user__localBody=localbody_param, category=PostCategory.ADVERTISEMENT, is_ad_approved=True)
            else:
                ads_queryset = Post.objects.filter(pincode=user.pincode, category=PostCategory.ADVERTISEMENT, is_ad_approved=True)

            ads_queryset = ads_queryset.order_by('-created_at')
            ads_serializer = AdSerializer(ads_queryset[:10], many=True, context={'request': request})

            # Get paginated response with cursor links
            response = paginator.get_paginated_response(post_serializer.data)

            # Add ads to the response data
            response.data['ads'] = ads_serializer.data

            return Response({
                "status": 200,
                "data": response.data
            })

        # Fallback (shouldn't happen with cursor pagination)
        post_serializer = PostSerializer(queryset, many=True, context={'request': request})
        return Response({
            "status": 200,
            "data": {
                "posts": post_serializer.data,
                "ads": []
            }
        }) 

# Refresh endpoint logic can basically reuse FeedAPIView or similar
class DeleteAccountAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        user_id = str(user.id)

        # Delete the user (CASCADE will delete all related posts, comments, votes, reports, etc.)
        user.delete()

        return Response({
            "status": 200,
            "message": "Account deleted successfully",
            "data": {
                "userId": user_id
            }
        }, status=status.HTTP_200_OK)

class GenerateUploadURLAPIView(APIView):
    """
    Generate signed upload URL for Supabase Storage
    Flutter app will use this to upload images directly to Supabase
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .supabase_storage import generate_signed_upload_url, generate_unique_filename
        
        filename = request.data.get('filename')
        content_type = request.data.get('content_type', 'image/jpeg')
        
        if not filename:
            return Response({
                "status": 400,
                "message": "filename is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Generate unique file path
            file_path = generate_unique_filename(filename, prefix="posts")
            
            # Generate signed upload URL
            upload_data = generate_signed_upload_url(file_path)
            
            return Response({
                "status": 200,
                "data": {
                    "upload_url": upload_data['signed_url'],
                    "file_path": upload_data['file_path'],
                    "public_url": upload_data['public_url'],
                    "expires_in": upload_data.get('expires_in', 3600)
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": 500,
                "message": f"Failed to generate upload URL: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
