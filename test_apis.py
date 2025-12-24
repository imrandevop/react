#!/usr/bin/env python3
"""
Comprehensive API Test Script for Django REST Application
Tests all endpoints to ensure they're working correctly
"""

import requests
import json
import uuid
from datetime import datetime
import os

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_USER_DATA = {
    "userId": str(uuid.uuid4()),
    "localBody": "Test City",
    "pincode": "123456"
}

# Store test data
test_context = {
    "token": None,
    "user_id": None,
    "post_id": None,
    "comment_id": None,
}

# Test results tracker
test_results = []

def log_test(endpoint, method, status, expected_status, message="", details=None):
    """Log test result"""
    success = status == expected_status
    result = {
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "expected": expected_status,
        "success": success,
        "message": message,
        "details": details
    }
    test_results.append(result)
    
    symbol = "✓" if success else "✗"
    print(f"{symbol} {method} {endpoint} - Status: {status} (Expected: {expected_status})")
    if message:
        print(f"  Message: {message}")
    if not success and details:
        print(f"  Details: {details}")
    return success

def get_headers():
    """Get authorization headers"""
    if test_context["token"]:
        return {
            "Authorization": f"Bearer {test_context['token']}",
            "Content-Type": "application/json"
        }
    return {"Content-Type": "application/json"}

# ============================================================================
# TEST 1: Login/Authentication API
# ============================================================================
def test_login():
    """Test POST /api/auth/login"""
    print("\n" + "="*70)
    print("TEST 1: Login/Authentication API")
    print("="*70)
    
    url = f"{BASE_URL}/auth/login"
    
    try:
        response = requests.post(url, json=TEST_USER_DATA)
        data = response.json()
        
        if log_test("/auth/login", "POST", response.status_code, 200, "Login successful"):
            # Store token for subsequent requests
            test_context["token"] = data.get("data", {}).get("token")
            test_context["user_id"] = data.get("data", {}).get("user", {}).get("id")
            print(f"  Token acquired: {test_context['token'][:20]}...")
            print(f"  User ID: {test_context['user_id']}")
            return True
        else:
            print(f"  Response: {data}")
            return False
    except Exception as e:
        log_test("/auth/login", "POST", 0, 200, f"Exception: {str(e)}")
        return False

# ============================================================================
# TEST 2: Create Post
# ============================================================================
def test_create_post():
    """Test POST /api/posts"""
    print("\n" + "="*70)
    print("TEST 2: Create Post API")
    print("="*70)
    
    url = f"{BASE_URL}/posts/"
    
    # Test creating different types of posts
    post_types = [
        {"category": "NEWS", "headline": "Test News", "description": "This is a test news post"},
        {"category": "UPDATE", "headline": "Test Update", "description": "This is a test update post"},
    ]
    
    for post_data in post_types:
        try:
            response = requests.post(url, json=post_data, headers=get_headers())
            data = response.json()
            
            if log_test("/posts/", "POST", response.status_code, 201, f"Created {post_data['category']} post"):
                if not test_context["post_id"]:  # Store first post ID
                    test_context["post_id"] = data.get("data", {}).get("id")
                    print(f"  Stored Post ID: {test_context['post_id']}")
        except Exception as e:
            log_test("/posts/", "POST", 0, 201, f"Exception: {str(e)}")
    
    return test_context["post_id"] is not None

# ============================================================================
# TEST 3: Get Posts List
# ============================================================================
def test_get_posts():
    """Test GET /api/posts"""
    print("\n" + "="*70)
    print("TEST 3: Get Posts List API")
    print("="*70)
    
    url = f"{BASE_URL}/posts/"
    
    try:
        response = requests.get(url, headers=get_headers())
        data = response.json()
        
        if log_test("/posts/", "GET", response.status_code, 200, "Retrieved posts list"):
            posts = data.get("data", []) if isinstance(data.get("data"), list) else data.get("results", [])
            print(f"  Total posts retrieved: {len(posts)}")
            return True
    except Exception as e:
        log_test("/posts/", "GET", 0, 200, f"Exception: {str(e)}")
    
    return False

# ============================================================================
# TEST 4: Get Single Post
# ============================================================================
def test_get_single_post():
    """Test GET /api/posts/{id}"""
    print("\n" + "="*70)
    print("TEST 4: Get Single Post API")
    print("="*70)
    
    if not test_context["post_id"]:
        print("  Skipping: No post ID available")
        return False
    
    url = f"{BASE_URL}/posts/{test_context['post_id']}/"
    
    try:
        response = requests.get(url, headers=get_headers())
        data = response.json()
        
        return log_test(f"/posts/{test_context['post_id']}/", "GET", response.status_code, 200, "Retrieved single post")
    except Exception as e:
        log_test(f"/posts/{test_context['post_id']}/", "GET", 0, 200, f"Exception: {str(e)}")
    
    return False

# ============================================================================
# TEST 5: Update Post
# ============================================================================
def test_update_post():
    """Test PUT /api/posts/{id}"""
    print("\n" + "="*70)
    print("TEST 5: Update Post API")
    print("="*70)
    
    if not test_context["post_id"]:
        print("  Skipping: No post ID available")
        return False
    
    url = f"{BASE_URL}/posts/{test_context['post_id']}/"
    update_data = {
        "category": "NEWS",
        "headline": "Updated Test News",
        "description": "This post has been updated"
    }
    
    try:
        response = requests.put(url, json=update_data, headers=get_headers())
        data = response.json()
        
        return log_test(f"/posts/{test_context['post_id']}/", "PUT", response.status_code, 200, "Post updated successfully")
    except Exception as e:
        log_test(f"/posts/{test_context['post_id']}/", "PUT", 0, 200, f"Exception: {str(e)}")
    
    return False

# ============================================================================
# TEST 6: Voting APIs (Upvote/Downvote)
# ============================================================================
def test_voting():
    """Test POST /api/posts/{id}/upvote and /api/posts/{id}/downvote"""
    print("\n" + "="*70)
    print("TEST 6: Voting APIs")
    print("="*70)
    
    if not test_context["post_id"]:
        print("  Skipping: No post ID available")
        return False
    
    # Test upvote
    upvote_url = f"{BASE_URL}/posts/{test_context['post_id']}/upvote/"
    try:
        response = requests.post(upvote_url, headers=get_headers())
        data = response.json()
        
        if log_test(f"/posts/{test_context['post_id']}/upvote/", "POST", response.status_code, 200, "Upvote successful"):
            print(f"  Upvotes: {data.get('data', {}).get('upvotes', 0)}")
            print(f"  Has upvoted: {data.get('data', {}).get('hasUpvoted', False)}")
    except Exception as e:
        log_test(f"/posts/{test_context['post_id']}/upvote/", "POST", 0, 200, f"Exception: {str(e)}")
    
    # Test downvote
    downvote_url = f"{BASE_URL}/posts/{test_context['post_id']}/downvote/"
    try:
        response = requests.post(downvote_url, headers=get_headers())
        data = response.json()
        
        if log_test(f"/posts/{test_context['post_id']}/downvote/", "POST", response.status_code, 200, "Downvote successful"):
            print(f"  Downvotes: {data.get('data', {}).get('downvotes', 0)}")
            print(f"  Has downvoted: {data.get('data', {}).get('hasDownvoted', False)}")
    except Exception as e:
        log_test(f"/posts/{test_context['post_id']}/downvote/", "POST", 0, 200, f"Exception: {str(e)}")
    
    return True

# ============================================================================
# TEST 7: Comments APIs
# ============================================================================
def test_comments():
    """Test comment CRUD operations"""
    print("\n" + "="*70)
    print("TEST 7: Comments APIs")
    print("="*70)
    
    if not test_context["post_id"]:
        print("  Skipping: No post ID available")
        return False
    
    # Create comment
    create_url = f"{BASE_URL}/posts/{test_context['post_id']}/comments/"
    comment_data = {"text": "This is a test comment"}
    
    try:
        response = requests.post(create_url, json=comment_data, headers=get_headers())
        data = response.json()
        
        if log_test(f"/posts/{test_context['post_id']}/comments/", "POST", response.status_code, 201, "Comment created"):
            test_context["comment_id"] = data.get("id")
            print(f"  Comment ID: {test_context['comment_id']}")
    except Exception as e:
        log_test(f"/posts/{test_context['post_id']}/comments/", "POST", 0, 201, f"Exception: {str(e)}")
    
    # Get comments
    try:
        response = requests.get(create_url, headers=get_headers())
        data = response.json()
        
        if log_test(f"/posts/{test_context['post_id']}/comments/", "GET", response.status_code, 200, "Retrieved comments"):
            print(f"  Number of comments: {len(data) if isinstance(data, list) else 0}")
    except Exception as e:
        log_test(f"/posts/{test_context['post_id']}/comments/", "GET", 0, 200, f"Exception: {str(e)}")
    
    # Update comment
    if test_context["comment_id"]:
        update_url = f"{BASE_URL}/posts/{test_context['post_id']}/update_comment/"
        update_data = {
            "comment_id": test_context["comment_id"],
            "text": "Updated comment text"
        }
        
        try:
            response = requests.put(update_url, json=update_data, headers=get_headers())
            log_test(f"/posts/{test_context['post_id']}/update_comment/", "PUT", response.status_code, 200, "Comment updated")
        except Exception as e:
            log_test(f"/posts/{test_context['post_id']}/update_comment/", "PUT", 0, 200, f"Exception: {str(e)}")
    
    return True

# ============================================================================
# TEST 8: Feed APIs
# ============================================================================
def test_feed_apis():
    """Test feed endpoints with different tabs"""
    print("\n" + "="*70)
    print("TEST 8: Feed APIs")
    print("="*70)
    
    tabs = ["All", "Today", "Problems", "Updates", "Yours"]
    
    for tab in tabs:
        url = f"{BASE_URL}/feed?tab={tab}"
        
        try:
            response = requests.get(url, headers=get_headers())
            data = response.json()
            
            if log_test(f"/feed?tab={tab}", "GET", response.status_code, 200, f"Feed retrieved for {tab} tab"):
                feed_data = data.get("data", {})
                posts = feed_data.get("results", []) if "results" in feed_data else feed_data.get("posts", [])
                ads = feed_data.get("ads", [])
                print(f"  Posts: {len(posts)}, Ads: {len(ads)}")
        except Exception as e:
            log_test(f"/feed?tab={tab}", "GET", 0, 200, f"Exception: {str(e)}")
    
    return True

# ============================================================================
# TEST 9: Feed Refresh API
# ============================================================================
def test_feed_refresh():
    """Test feed refresh endpoint"""
    print("\n" + "="*70)
    print("TEST 9: Feed Refresh API")
    print("="*70)
    
    url = f"{BASE_URL}/feed/refresh?tab=All"
    
    try:
        response = requests.get(url, headers=get_headers())
        data = response.json()
        
        if log_test("/feed/refresh?tab=All", "GET", response.status_code, 200, "Feed refresh successful"):
            posts = data.get("data", {}).get("posts", [])
            print(f"  Posts refreshed: {len(posts)}")
            return True
    except Exception as e:
        log_test("/feed/refresh?tab=All", "GET", 0, 200, f"Exception: {str(e)}")
    
    return False

# ============================================================================
# TEST 10: Report Post API
# ============================================================================
def test_report_post():
    """Test POST /api/posts/{id}/report"""
    print("\n" + "="*70)
    print("TEST 10: Report Post API")
    print("="*70)
    
    if not test_context["post_id"]:
        print("  Skipping: No post ID available")
        return False
    
    url = f"{BASE_URL}/posts/{test_context['post_id']}/report/"
    report_data = {"description": "This post contains inappropriate content"}
    
    try:
        response = requests.post(url, json=report_data, headers=get_headers())
        data = response.json()
        
        if log_test(f"/posts/{test_context['post_id']}/report/", "POST", response.status_code, 201, "Post reported successfully"):
            print(f"  Total reports: {data.get('data', {}).get('total_reports', 0)}")
            return True
    except Exception as e:
        log_test(f"/posts/{test_context['post_id']}/report/", "POST", 0, 201, f"Exception: {str(e)}")
    
    return False

# ============================================================================
# TEST 11: Delete Comment
# ============================================================================
def test_delete_comment():
    """Test DELETE /api/posts/{id}/delete_comment"""
    print("\n" + "="*70)
    print("TEST 11: Delete Comment API")
    print("="*70)
    
    if not test_context["post_id"] or not test_context["comment_id"]:
        print("  Skipping: No post ID or comment ID available")
        return False
    
    url = f"{BASE_URL}/posts/{test_context['post_id']}/delete_comment/"
    
    try:
        response = requests.delete(url, json={"comment_id": test_context["comment_id"]}, headers=get_headers())
        return log_test(f"/posts/{test_context['post_id']}/delete_comment/", "DELETE", response.status_code, 200, "Comment deleted")
    except Exception as e:
        log_test(f"/posts/{test_context['post_id']}/delete_comment/", "DELETE", 0, 200, f"Exception: {str(e)}")
    
    return False

# ============================================================================
# TEST 12: Delete Post
# ============================================================================
def test_delete_post():
    """Test DELETE /api/posts/{id}"""
    print("\n" + "="*70)
    print("TEST 12: Delete Post API")
    print("="*70)
    
    if not test_context["post_id"]:
        print("  Skipping: No post ID available")
        return False
    
    url = f"{BASE_URL}/posts/{test_context['post_id']}/"
    
    try:
        response = requests.delete(url, headers=get_headers())
        return log_test(f"/posts/{test_context['post_id']}/", "DELETE", response.status_code, 200, "Post deleted successfully")
    except Exception as e:
        log_test(f"/posts/{test_context['post_id']}/", "DELETE", 0, 200, f"Exception: {str(e)}")
    
    return False

# ============================================================================
# TEST 13: Delete Account API
# ============================================================================
def test_delete_account():
    """Test DELETE /api/auth/delete-account"""
    print("\n" + "="*70)
    print("TEST 13: Delete Account API")
    print("="*70)
    
    url = f"{BASE_URL}/auth/delete-account"
    
    try:
        response = requests.delete(url, headers=get_headers())
        return log_test("/auth/delete-account", "DELETE", response.status_code, 200, "Account deleted successfully")
    except Exception as e:
        log_test("/auth/delete-account", "DELETE", 0, 200, f"Exception: {str(e)}")
    
    return False

# ============================================================================
# Main Test Runner
# ============================================================================
def print_summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r["success"])
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    if failed > 0:
        print("Failed Tests:")
        for r in test_results:
            if not r["success"]:
                print(f"  ✗ {r['method']} {r['endpoint']} - Status: {r['status']} (Expected: {r['expected']})")
                if r["message"]:
                    print(f"    {r['message']}")

def main():
    """Main test runner"""
    print("="*70)
    print("DJANGO REST API COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_DATA['localBody']} ({TEST_USER_DATA['pincode']})")
    print("="*70)
    
    # Run all tests in sequence
    test_login()
    test_create_post()
    test_get_posts()
    test_get_single_post()
    test_update_post()
    test_voting()
    test_comments()
    test_feed_apis()
    test_feed_refresh()
    test_report_post()
    test_delete_comment()
    test_delete_post()
    test_delete_account()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()
