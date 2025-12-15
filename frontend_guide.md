# 📱 Frontend Implementation Guide

This guide defines the integration points for the Flutter Frontend using the Django Backend.

**Base URL**: `http://142.93.215.250/api`

---

## 🔐 1. Authentication (Login)
- **Screen**: Login
- **Inputs**: `Local Body` (Text), `Pincode` (6 digits)
- **Action**: `POST /auth/login`
- **Body**:
  ```json
  {
    "localBody": "user_identifier",
    "pincode": "123456"
  }
  ```
- **Success**:
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
- **Data Handling**:
  - **Posts List**: Render the `data.posts` array.
  - **Ads Injection**:
    - The API returns `data.ads` separately.
    - **Frontend Logic**: Insert one Ad card into the list after every 4-5 posts.
    - **Ad Card**: Show `sponsorName` badge, `headline` (title), and `buttonText`.

---

## ✏️ 3. Create Post
- **Screen**: Floating Action Button -> New Post Form
- **Fields**:
  - **Category**: Dropdown (`NEWS`, `UPDATE`, `PROBLEM`, `ADVERTISEMENT`)
  - **Headline**: Optional text.
  - **Description**: Required text.
  - **Images**: Picker (Max 10).
- **Validation**:
  - ⚠️ If Category is **PROBLEM**, at least **one image is MANDATORY**.
- **Action**: `POST /api/posts/`
- **Format**: `multipart/form-data`

---

## 👍 4. Post Interactions
### Voting
- **UI**: Up arrow (Upvote), Down arrow (Downvote).
- **State**: Check `hasUpvoted` / `hasDownvoted` to color icons (e.g., Orange/Blue).
- **Actions**:
  - **Upvote**: `POST /api/posts/{id}/upvote/`
  - **Downvote**: `POST /api/posts/{id}/downvote/`
- **Logic**: Backend handles toggling. Just call the API and update the local count/state from the response.

### Edit / Delete
- **Visibility**: Only show Edit/Delete buttons if `userId` matches the logged-in user's ID.
- **Edit**: `PUT /api/posts/{id}/` (Send full data).
- **Delete**: `DELETE /api/posts/{id}/`.

---

## 🧩 Data Models (Reference)

### **Post Object**
```json
{
  "id": "1",
  "userId": "5",
  "userLocalBody": "Name of User",
  "category": "PROBLEM",
  "headline": "Road Broken",
  "description": "Details here...",
  "imageUrls": ["http://.../img.jpg"],
  "upvotes": 10,
  "downvotes": 2,
  "hasUpvoted": true,
  "hasDownvoted": false,
  "createdAt": "2025-12-15T..."
}
```

### **Ad Object**
```json
{
  "id": "5",
  "title": "Buy Shoes",
  "sponsorName": "Nike Local",
  "buttonText": "Shop Now",
  "buttonUrl": "https://nike.com",
  "imageUrls": ["..."]
}
```
