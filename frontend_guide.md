# 📱 Frontend Implementation Guide

This guide defines the integration points for the Flutter Frontend using the Django Backend.

**Base URL**: `http://142.93.215.250/api`

---

## 🔐 1. Authentication (Login)
- **Screen**: Login
- **Inputs**: `Local Body` (Text), `Pincode` (6 digits)
- **Action**: `POST /auth/login`
- **Request Body**:
  ```json
  {
    "localBody": "user_identifier",
    "pincode": "123456"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
      "status": 200,
      "data": {
          "token": "eyJ0eX...",
          "user": {
              "id": "1",
              "localBody": "user_identifier",
              "pincode": "123456"
          }
      }
  }
  ```
- **Success Handling**:
  - Save `token` securely (SecureStorage / SharedPrefs).
  - Attach header to **ALL** subsequent requests: `Authorization: Bearer <token>`
  - Navigate to Home Feed.

---

## 📰 2. Home Feed
- **Screen**: Main Tab View
- **Tabs**: `All` | `Today` | `Problems` | `Updates` | `Yours`
- **Action**: `GET /api/feed`
- **Query Params**:
  - `tab`: (Required) One of the tab names above.
  - `page`: (Optional) For pagination (Default: 1).
- **Response (200 OK)**:
  ```json
  {
      "status": 200,
      "data": {
          "posts": [
              {
                  "id": "10",
                  "userId": "5",
                  "headline": "Road Broken",
                  "description": "Fix this please",
                  "imageUrls": ["http://.../img.jpg"],
                  "category": "PROBLEM",
                  "upvotes": 10,
                  "downvotes": 2,
                  "commentsCount": 0,
                  "createdAt": "2025-12-15T12:00:00Z",
                  "hasUpvoted": true,
                  "hasDownvoted": false
              }
          ],
          "ads": [
              {
                  "id": "55",
                  "title": "Nike Sale",
                  "description": "50% Off",
                  "imageUrls": ["http://.../ad.jpg"],
                  "buttonText": "Shop Now",
                  "buttonUrl": "https://nike.com",
                  "sponsorName": "Nike Local"
              }
          ]
      }
  }
  ```
- **Frontend Logic**:
  - Render `data.posts` as the main list.
  - Inject one item from `data.ads` after every 4-5 posts using your local list adapter.

---

## ✏️ 3. Create Post
- **Screen**: New Post Form
- **Action**: `POST /api/posts/`
- **Format**: `multipart/form-data`
- **Validation**:
  - `category` (Required): `NEWS`, `UPDATE`, `PROBLEM`, `ADVERTISEMENT`
  - `description` (Required)
  - `images` (List of Files): **Mandatory** if category is `PROBLEM`.
- **Request Body (Form Data)**:
  - `category`: "PROBLEM"
  - `headline`: "Broken Pipe"
  - `description`: "Water everywhere"
  - `images`: [File1, File2]
- **Response (201 Created)**:
  ```json
  {
      "status": 201,
      "data": {
          "id": "12",
          "userId": "1",
          "headline": "Broken Pipe",
          "category": "PROBLEM",
          ...
      }
  }
  ```

---

## 👍 4. Post Interactions

### Voting
- **Actions**:
  - **Upvote**: `POST /api/posts/{id}/upvote/`
  - **Downvote**: `POST /api/posts/{id}/downvote/`
- **Response (200 OK)**:
  ```json
  {
      "status": 200,
      "data": {
          "upvotes": 11,
          "downvotes": 2,
          "hasUpvoted": true,
          "hasDownvoted": false
      }
  }
  ```
- **Logic**: Backend handles toggling. Just call API and update UI with returned counts/colors.

### Edit Post
- **Action**: `PUT /api/posts/{id}/` (Multipart)
- **Request**:
  - `headline`: "Updated Title"
  - `description`: "Updated Desc"
  - `images`: [New Files] (Replaces old images entirely if sent)
- **Response**: Returns updated Post object (Same as Create).

### Delete Post
- **Action**: `DELETE /api/posts/{id}/`
- **Response (200 OK)**:
  ```json
  {
      "status": 200,
      "message": "Post deleted successfully"
  }
  ```

---

## 💬 5. Comments

### List Comments
- **Screen**: Post Detail / Comment Section
- **Action**: `GET /api/posts/{id}/comments/`
- **Response (200 OK)**:
  ```json
  [
      {
          "id": 1,
          "user": "KOL123",
          "userId": "5",
          "text": "This is a comment",
          "created_at": "2025-12-15T10:30:00Z"
      },
      {
          "id": 2,
          "user": "DEL456",
          "userId": "8",
          "text": "Another comment",
          "created_at": "2025-12-15T11:00:00Z"
      }
  ]
  ```
- **Frontend Logic**:
  - Comments are ordered **oldest first** (chronological, like a conversation).
  - Display all comments without pagination.

### Add Comment
- **Screen**: Post Detail / Comment Input
- **Action**: `POST /api/posts/{id}/comments/`
- **Request Body**:
  ```json
  {
      "text": "My comment text"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
      "id": 3,
      "user": "KOL123",
      "userId": "5",
      "text": "My comment text",
      "created_at": "2025-12-15T12:00:00Z"
  }
  ```
- **Validation**:
  - `text` must not be empty or whitespace only.

### Update Comment
- **Screen**: Comment Item (Edit Mode)
- **Action**: `PUT /api/posts/{id}/update_comment/`
- **Request Body**:
  ```json
  {
      "comment_id": 3,
      "text": "Updated comment text"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
      "id": 3,
      "user": "KOL123",
      "userId": "5",
      "text": "Updated comment text",
      "created_at": "2025-12-15T12:00:00Z"
  }
  ```
- **Permission**: Only the comment author can edit their own comments.
- **Error (403 Forbidden)**:
  ```json
  {
      "error": "You can only edit your own comments"
  }
  ```

### Delete Comment
- **Screen**: Comment Item (Delete Option)
- **Action**: `DELETE /api/posts/{id}/delete_comment/`
- **Request Body** (or Query Params):
  ```json
  {
      "comment_id": 3
  }
  ```
- **Response (200 OK)**:
  ```json
  {
      "message": "Comment deleted successfully"
  }
  ```
- **Permission**: Only the comment author can delete their own comments.
- **Error (403 Forbidden)**:
  ```json
  {
      "error": "You can only delete your own comments"
  }
  ```

---

## 🧩 Data Models (Reference)

### **Post Object**
```json
{
  "id": "1",
  "userId": "5",
  "headline": "Road Broken",
  "description": "Details here...",
  "imageUrls": ["http://.../img.jpg"],
  "category": "PROBLEM",
  "upvotes": 10,
  "downvotes": 2,
  "commentsCount": 5,
  "createdAt": "2025-12-15T...",
  "hasUpvoted": true,
  "hasDownvoted": false
}
```

### **Ad Object**
```json
{
  "id": "5",
  "title": "Buy Shoes",
  "description": "Best shoes ever",
  "sponsorName": "Nike Local",
  "buttonText": "Shop Now",
  "buttonUrl": "https://nike.com",
  "imageUrls": ["http://.../ad.jpg"]
}
```

### **Comment Object**
```json
{
  "id": 1,
  "user": "KOL123",
  "userId": "5",
  "text": "This is a comment",
  "created_at": "2025-12-15T10:30:00Z"
}
```
