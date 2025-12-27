# Final Sorting Configuration

## ✅ What You Have Now

### **"Today" Tab** 🔥
- **Sorting:** Reddit-style Hot Score (upvotes + downvotes + time decay)
- **Pagination:** CursorPagination
- **Purpose:** Show trending posts from today

### **All Other Tabs** 📱 (All, Problems, Updates, Yours)
- **Sorting:** Instagram-style Newest First
- **Pagination:** CursorPagination
- **Purpose:** Show most recent content

---

## 📊 Sorting Breakdown

| Tab | Sort Method | Example Order |
|-----|-------------|---------------|
| **Today** | Hot Score (Reddit) | Post with 50 upvotes (2 hrs ago) > Post with 5 upvotes (30 mins ago) |
| **All** | Newest First | Posted 1 min ago > Posted 1 hour ago > Posted 1 day ago |
| **Problems** | Newest First | Most recent problem > Older problem |
| **Updates** | Newest First | Latest update > Previous update |
| **Yours** | Newest First | Your newest post > Your older post |

---

## 🎯 "Today" Tab Behavior

### **How Hot Score Works:**

Posts from **today only** are ranked by:
1. **Upvotes boost score** (logarithmic)
2. **Downvotes reduce score** (logarithmic)
3. **Time factor** (newer = slightly higher base)

**Example Timeline (all from today):**

| Time Posted | Upvotes | Downvotes | Hot Score | Position |
|-------------|---------|-----------|-----------|----------|
| 2 hours ago | 50 | 5 | 38.8 | **1st** 🔥 |
| 30 mins ago | 15 | 0 | 38.2 | **2nd** |
| 5 mins ago | 5 | 0 | 37.7 | **3rd** |
| 1 hour ago | 2 | 1 | 37.5 | 4th |
| Just now | 0 | 0 | 37.4 | 5th |

**Key Points:**
- Only shows posts from **current day** (midnight to midnight)
- Upvoted content rises to top
- Fresh posts with good engagement beat older posts
- Downvotes matter (reduce ranking)

---

## 📱 Other Tabs Behavior (Instagram-Style)

### **Simple Newest First:**

| Time Posted | Upvotes | Position |
|-------------|---------|----------|
| 1 min ago | 0 | **1st** |
| 1 hour ago | 100 | **2nd** |
| 1 day ago | 500 | **3rd** |
| 1 week ago | 1000 | **4th** |

**Upvotes don't affect ranking** - only creation time matters!

---

## 🔄 Setup Required

### **Step 1: Run Migration**

```bash
source venv/bin/activate
python manage.py migrate
```

### **Step 2: Calculate Initial Hot Scores**

```bash
python manage.py update_hot_scores --days 1
```

*(Only need scores for today's posts)*

### **Step 3: Set Up Hourly Cron Job** (Important for "Today" tab)

```bash
crontab -e
```

Add this line:
```
0 * * * * cd /home/imran/Desktop/REACT && source venv/bin/activate && python manage.py update_hot_scores --days 1
```

This updates hot scores every hour for posts from the last 24 hours.

---

## 🚀 API Usage

### **All Tabs Use Cursor Pagination:**

```bash
# First page
GET /api/feed?tab=Today

# Next page (use cursor from response)
GET /api/feed?tab=Today&cursor=cD0yMDI1...
```

### **Response Format:**

```json
{
  "next": "http://localhost:8000/api/feed?cursor=cD0yMDI1...",
  "previous": null,
  "results": [
    {
      "id": "...",
      "headline": "...",
      "upvotes": 50,
      "downvotes": 5,
      "created_at": "2025-12-27T14:30:00Z",
      ...
    }
  ]
}
```

---

## 💡 Why This Configuration?

### **"Today" Tab with Hot Score:**
- ✅ **Trending content rises** - Important issues get visibility
- ✅ **Quality over recency** - Good posts stay visible all day
- ✅ **Community engagement** - Upvotes/downvotes matter
- ✅ **Fresh discovery** - New posts can compete

### **Other Tabs with Newest First:**
- ✅ **Simple and predictable** - Users know what to expect
- ✅ **Instagram-style UX** - Familiar pattern
- ✅ **Performance** - No complex calculations needed
- ✅ **Always fresh** - Latest content always on top

---

## 🎛️ Configuration Files

### **Pagination Classes** ([views.py:46-60](basic/views.py#L46-L60))

```python
class FeedNewestCursorPagination(CursorPagination):
    """Instagram-style: Newest first"""
    ordering = '-created_at'

class FeedHotCursorPagination(CursorPagination):
    """Reddit-style: Hot score (for Today tab only)"""
    ordering = '-hot_score'
```

### **Tab Logic** ([views.py:382-408](basic/views.py#L382-L408))

```python
if tab_mapped == "All":
    queryset = queryset.order_by('-created_at')
    paginator = FeedNewestCursorPagination()

elif tab_mapped == "Today":
    queryset = queryset.filter(created_at__date=now.date()).order_by('-hot_score', '-created_at')
    paginator = FeedHotCursorPagination()

elif tab_mapped == "Problems":
    queryset = queryset.filter(category=PostCategory.PROBLEM).order_by('-created_at')
    paginator = FeedNewestCursorPagination()

# ... etc
```

---

## 🧪 Testing

### **Test "Today" Tab (Hot Score):**

```bash
# Create a post
curl -X POST http://localhost:8000/api/posts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "NEWS",
    "description": "Test post",
    "image_urls": []
  }'

# Upvote it
curl -X POST http://localhost:8000/api/posts/{POST_ID}/upvote/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check Today feed (post should be at top)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/feed?tab=Today"
```

### **Test Other Tabs (Newest First):**

```bash
# Check All feed (newest post first, regardless of votes)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/feed?tab=All"
```

---

## 📈 Performance

### **"Today" Tab:**
- Uses `hot_score` index (fast)
- Only queries today's posts (small dataset)
- CursorPagination (efficient)

### **Other Tabs:**
- Uses `created_at` index (fast)
- CursorPagination (efficient)
- No calculations needed (simple sort)

---

## 🔧 Maintenance

### **Daily Tasks:**
- ✅ Cron updates hot scores hourly (automatic)

### **Weekly Tasks:**
- Check cron is running: `crontab -l`
- Verify scores are updating: `python manage.py update_hot_scores --days 1`

### **No Maintenance Needed:**
- Other tabs (newest first) - no background jobs required

---

## 🆚 Comparison

### **Before vs After:**

| Tab | Before | After |
|-----|--------|-------|
| **Today** | Upvotes only | Hot score (upvotes + time decay) |
| **All** | Upvotes only | Newest first |
| **Problems** | Upvotes only | Newest first |
| **Updates** | Upvotes only | Newest first |
| **Yours** | Newest first | Newest first (unchanged) |

---

## ✨ Summary

✅ **"Today" tab** → Reddit-style ranking (quality + engagement)
✅ **All other tabs** → Instagram-style (newest first)
✅ **All tabs** → CursorPagination (better performance)
✅ **Automatic updates** → Hot scores recalculate hourly
✅ **Simple & predictable** → Users get expected behavior

**Best of both worlds!** 🎉

---

## 🚨 Important

1. ✅ Run migration: `python manage.py migrate`
2. ✅ Calculate scores: `python manage.py update_hot_scores --days 1`
3. ✅ Set up cron: Update scores hourly for "Today" tab
4. ✅ Test both "Today" and "All" tabs to see different sorting

---

## 📞 Quick Reference

```bash
# Setup
python manage.py migrate
python manage.py update_hot_scores --days 1

# Set cron
crontab -e
# Add: 0 * * * * cd /home/imran/Desktop/REACT && source venv/bin/activate && python manage.py update_hot_scores --days 1

# Test
curl -H "Authorization: Bearer TOKEN" "http://localhost:8000/api/feed?tab=Today"
curl -H "Authorization: Bearer TOKEN" "http://localhost:8000/api/feed?tab=All"
```

Done! 🚀
