from rest_framework.views import APIView
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from django.utils import timezone
from .models import Post, PostCategory, Vote, Comment
from .serializers import LoginSerializer, PostSerializer, PostCreateUpdateSerializer, AdSerializer, CommentSerializer

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

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100

class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
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
            queryset = queryset.filter(created_at__date=now.date()).order_by('-created_at')
        elif filter_param == 'PROBLEMS':
            queryset = queryset.filter(category=PostCategory.PROBLEM).order_by('-created_at')
        elif filter_param == 'UPDATES':
            queryset = queryset.filter(category=PostCategory.UPDATE).order_by('-created_at')
        elif filter_param == 'YOURS':
            queryset = queryset.filter(user=request.user).order_by('-created_at')
        else: 
             queryset = queryset.annotate(
                upvote_count=Count('votes', filter=Q(votes__vote_type=Vote.UPVOTE))
            ).order_by('-upvote_count', '-created_at')

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
            return Response(serializer.data)

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
        
        # Base Filter: Pincode Isolation
        queryset = Post.objects.filter(pincode=user.pincode)
        
        # Filter out ADVERTISEMENTS from main post stream (as discussed)
        queryset = queryset.exclude(category=PostCategory.ADVERTISEMENT)
        
        # Tab Logic
        # Common Sorting: Highest Upvotes, then Newest
        # Except 'Yours' which is Newest First
        
        if tab_mapped == "All":
             queryset = queryset.annotate(
                upvote_count=Count('votes', filter=Q(votes__vote_type=Vote.UPVOTE))
            ).order_by('-upvote_count', '-created_at')
            
        elif tab_mapped == "Today":
             now = timezone.now()
             queryset = queryset.filter(created_at__date=now.date()).annotate(
                upvote_count=Count('votes', filter=Q(votes__vote_type=Vote.UPVOTE))
            ).order_by('-upvote_count', '-created_at')
             
        elif tab_mapped == "Problems":
             queryset = queryset.filter(category=PostCategory.PROBLEM).annotate(
                upvote_count=Count('votes', filter=Q(votes__vote_type=Vote.UPVOTE))
            ).order_by('-upvote_count', '-created_at')
             
        elif tab_mapped == "Updates":
             queryset = queryset.filter(category=PostCategory.UPDATE).annotate(
                upvote_count=Count('votes', filter=Q(votes__vote_type=Vote.UPVOTE))
            ).order_by('-upvote_count', '-created_at')
             
        elif tab_mapped == "Yours":
             queryset = queryset.filter(user=user).order_by('-created_at')

        # Pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        post_serializer = PostSerializer(page, many=True, context={'request': request})
        
        # Ads Retrieval (Separate List)
        # "Ads appear in all tabs"
        # "Only admin-approved ADVERTISEMENT posts"
        ads_queryset = Post.objects.filter(
            pincode=user.pincode, # Ads also hyperlocal? Assuming yes based on "All feed endpoints... Filter posts strictly by user.pincode"
            category=PostCategory.ADVERTISEMENT,
            is_ad_approved=True
        ).order_by('-created_at') # Order doesn't matter much as frontend decides placement, but newest ads first is good
        
        # Limit number of ads returned? Prompt says "Returned separately... Ads appear in all tabs", 
        # doesn't specify limit. I'll return all available valid ads for the client to intersperse. 
        # Or maybe limit to reasonable number (e.g. 5) to save bandwidth.
        # Given "Frontend decides placement", I'll return a reasonable batch.
        ads_serializer = AdSerializer(ads_queryset[:10], many=True, context={'request': request})
        
        return Response({
            "status": 200,
            "data": {
                "posts": post_serializer.data,
                "ads": ads_serializer.data
            }
        }) 

# Refresh endpoint logic can basically reuse FeedAPIView or similar
class FeedRefreshAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tab = request.query_params.get('tab')
        if not tab:
             return Response({"status": 400, "message": "Tab parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Reuse logic? Or copy-paste for simplicity/independence.
        # "Returns latest posts based on tab... No pagination required"
        
        valid_tabs = ["All", "Today", "Problems", "Updates", "Yours"]
        tab_mapped = next((t for t in valid_tabs if t.lower() == tab.lower()), None)
        
        if not tab_mapped:
             return Response({"status": 400, "message": "Invalid feed tab"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        queryset = Post.objects.filter(pincode=user.pincode).exclude(category=PostCategory.ADVERTISEMENT)
        
        if tab_mapped == "All":
             queryset = queryset.annotate(upvote_count=Count('votes', filter=Q(votes__vote_type=Vote.UPVOTE))).order_by('-upvote_count', '-created_at')
        elif tab_mapped == "Today":
             now = timezone.now()
             queryset = queryset.filter(created_at__date=now.date()).annotate(upvote_count=Count('votes', filter=Q(votes__vote_type=Vote.UPVOTE))).order_by('-upvote_count', '-created_at')
        elif tab_mapped == "Problems":
             queryset = queryset.filter(category=PostCategory.PROBLEM).annotate(upvote_count=Count('votes', filter=Q(votes__vote_type=Vote.UPVOTE))).order_by('-upvote_count', '-created_at')
        elif tab_mapped == "Updates":
             queryset = queryset.filter(category=PostCategory.UPDATE).annotate(upvote_count=Count('votes', filter=Q(votes__vote_type=Vote.UPVOTE))).order_by('-upvote_count', '-created_at')
        elif tab_mapped == "Yours":
             queryset = queryset.filter(user=user).order_by('-created_at')
             
        # "No pagination required" - limiting to 20 for safety as agreed
        queryset = queryset[:20]
        
        serializer = PostSerializer(queryset, many=True, context={'request': request})
        
        # Doc doesn't say "ads" in refresh response, but usually refresh implies full view update.
        # "Returns latest posts" -> implies just posts. 
        # I will return just posts data wrapped.
        
        return Response({
            "status": 200,
            "data": {
                "posts": serializer.data
            }
        })
