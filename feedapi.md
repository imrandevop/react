● Feed API Documentation for Frontend

  Overview

  The Feed API provides two endpoints for fetching posts with cursor-based pagination and dynamic locality filtering.

  ---
  1. Feed Endpoint (Main Feed with Pagination)

  Endpoint

  GET /api/feed

  Authentication

  Required: Bearer Token (JWT)

  Query Parameters

  | Parameter | Type   | Required | Description                                          |
  |-----------|--------|----------|------------------------------------------------------|
  | tab       | string | ✅ Yes   | Feed tab type                                        |
  | pincode   | string | ❌ No    | Filter by specific pincode (highest priority)        |
  | localBody | string | ❌ No    | Filter by specific local body area                   |
  | cursor    | string | ❌ No    | Cursor token for pagination (from previous response) |
  | limit     | number | ❌ No    | Number of posts per page (default: 20, max: 100)     |

  Valid Tab Values

  - "All" - All posts sorted by upvotes
  - "Today" - Today's posts sorted by upvotes
  - "Problems" - Problem category posts sorted by upvotes
  - "Updates" - Update category posts sorted by upvotes
  - "Yours" - User's own posts sorted by newest first

  Locality Filter Priority Logic

  1. If pincode provided → Filter by pincode (highest priority)
  2. Else if localBody provided → Filter by localBody
  3. Else → Use authenticated user's pincode (default)

  Response Format

  Success (200)
  {
    "status": 200,
    "data": {
      "next": "http://api.example.com/api/feed?cursor=cD0yMDI1LTEy...",
      "previous": null,
      "results": [
        {
          "id": "uuid",
          "title": "Post title",
          "content": "Post content",
          "category": "PROBLEM",
          "pincode": "680001",
          "localBody": "Kochi",
          "user": {...},
          "upvotes": 15,
          "downvotes": 2,
          "hasUpvoted": false,
          "hasDownvoted": false,
          "commentsCount": 5,
          "created_at": "2025-12-23T10:30:00Z"
        }
      ],
      "ads": [
        {
          "id": "uuid",
          "title": "Ad title",
          "content": "Ad content",
          ...
        }
      ]
    }
  }

  Error (400)
  {
    "status": 400,
    "message": "Tab parameter is required"
  }

  Response Fields Explained

  | Field    | Type        | Description                                            |
  |----------|-------------|--------------------------------------------------------|
  | next     | string/null | URL with cursor for next page (null if last page)      |
  | previous | string/null | URL with cursor for previous page (null if first page) |
  | results  | array       | Array of post objects (max 20 by default)              |
  | ads      | array       | Array of advertisement posts (max 10)                  |

  ---
  2. Feed Refresh Endpoint (Pull-to-Refresh)

  Endpoint

  GET /api/feed/refresh

  Authentication

  Required: Bearer Token (JWT)

  Query Parameters

  | Parameter | Type   | Required | Description                                   |
  |-----------|--------|----------|-----------------------------------------------|
  | tab       | string | ✅ Yes   | Feed tab type (same as main feed)             |
  | pincode   | string | ❌ No    | Filter by specific pincode (highest priority) |
  | localBody | string | ❌ No    | Filter by specific local body area            |

  Note: No pagination parameters - always returns latest 20 posts

  Response Format

  Success (200)
  {
    "status": 200,
    "data": {
      "posts": [
        {
          "id": "uuid",
          "title": "Post title",
          ...
        }
      ]
    }
  }

  Note: Refresh endpoint does NOT return ads

  ---
  Frontend Implementation Guide

  Initial Load

  GET /api/feed?tab=All
  - Display results array
  - Intersperse ads array into the feed (frontend decides placement)
  - Store next cursor for pagination

  Load More (Infinite Scroll)

  GET /api/feed?tab=All&cursor={next_cursor}
  - Append new results to existing feed
  - Update next cursor
  - Continue until next is null

  Pull to Refresh

  GET /api/feed/refresh?tab=All
  - Replace current feed with fresh posts array
  - Reset pagination (discard old cursor)
  - Call main /api/feed again for pagination

  Change Locality

  GET /api/feed?tab=All&localBody=Kochi
  - Clear current feed
  - Load fresh feed for new locality
  - Store locality selection for subsequent requests

  Switch Tab

  GET /api/feed?tab=Problems
  - Clear current feed
  - Load new tab content
  - Reset pagination cursor

  ---
  Important Notes for Frontend

  ✅ DO's

  1. Always pass the same locality parameters (pincode or localBody) when paginating
  2. Store cursor token from next field for pagination
  3. Handle null next to disable "Load More" button (last page reached)
  4. Pass locality filter to both /api/feed and /api/feed/refresh
  5. Intersperse ads in the feed UI (backend returns them separately)

  ❌ DON'Ts

  1. Don't use page numbers - this is cursor-based, not page-based
  2. Don't expect ads in refresh endpoint response
  3. Don't mix different localities between pagination requests
  4. Don't parse cursor - treat it as opaque token

  Cursor Pagination Benefits

  - ✅ No duplicate posts when new content is added
  - ✅ Consistent results during pagination
  - ✅ Better performance for large datasets
  - ❌ Can't jump to specific page numbers

  ---
  Example Request Flow

  1. Initial Load
     GET /api/feed?tab=All
     → Returns: {next: "cursor123", results: [...20 posts], ads: [...]}

  2. User Scrolls Down
     GET /api/feed?tab=All&cursor=cursor123
     → Returns: {next: "cursor456", previous: "cursor123", results: [...20 more posts], ads: [...]}

  3. User Changes Locality
     GET /api/feed?tab=All&localBody=Kochi
     → Returns: {next: "cursor789", results: [...20 posts from Kochi], ads: [...]}

  4. User Scrolls in New Locality
     GET /api/feed?tab=All&localBody=Kochi&cursor=cursor789
     → Returns: {next: "cursor999", results: [...20 more Kochi posts], ads: [...]}

  5. User Pulls to Refresh
     GET /api/feed/refresh?tab=All&localBody=Kochi
     → Returns: {posts: [...latest 20 posts from Kochi]}

     Then call main feed again:
     GET /api/feed?tab=All&localBody=Kochi
     → Start fresh pagination

  ---
  Error Handling

  | Status | Message                     | Action                                |
  |--------|-----------------------------|---------------------------------------|
  | 400    | "Tab parameter is required" | Pass valid tab parameter              |
  | 400    | "Invalid feed tab"          | Use valid tab value                   |
  | 401    | Unauthorized                | Refresh auth token                    |
  | 404    | Invalid cursor              | Reset pagination, call without cursor |

  ---
  Testing Checklist

  - Initial feed load
  - Pagination (load more)
  - Pull to refresh
  - Tab switching (All, Today, Problems, Updates, Yours)
  - Locality filter by localBody
  - Locality filter by pincode
  - Pincode priority over localBody
  - Last page handling (next: null)
  - Ads display
  - Empty feed state