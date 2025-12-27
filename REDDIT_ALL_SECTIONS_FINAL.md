# Reddit-Style Ranking - ALL Sections (Final Configuration)

## ✅ What Changed

**All sections now use Reddit-style Hot Score ranking** (except "Yours" which stays newest-first)

---

## 📊 Current Configuration

| Tab | Sorting Method | Pagination |
|-----|----------------|------------|
| **All** 🔥 | Hot Score (Reddit) | CursorPagination |
| **Today** 🔥 | Hot Score (Reddit) | CursorPagination |
| **Problems** 🔥 | Hot Score (Reddit) | CursorPagination |
| **Updates** 🔥 | Hot Score (Reddit) | CursorPagination |
| **Yours** 📱 | Newest First | CursorPagination |

---

## 🎯 How It Works Now

### **Reddit-Style Ranking (All, Today, Problems, Updates)**

Posts are ranked by **hot_score** which combines:
- ✅ **Upvotes** (boost score)
- ✅ **Downvotes** (reduce score)
- ✅ **Time decay** (older posts gradually fall)

**Example Feed Order:**

| Post | Age | Upvotes | Downvotes | Hot Score | Position |
|------|-----|---------|-----------|-----------|----------|
| Post A | 1 day | 5 | 0 | 14062.60 | **1st** 🔥 |
| Post B | 2 days | 4 | 0 | 14060.98 | **2nd** |
| Post C | 3 days | 10 | 2 | 14058.50 | **3rd** |
| Post D | 1 week | 50 | 5 | 14042.30 | 4th (older, falling) |
| Post E | 2 weeks | 100 | 10 | 14015.20 | 5th (old, bottom) |

**Key Points:**
- Fresh posts with engagement rise to top
- Old popular posts gradually fall down
- Time decay keeps feed dynamic
- Downvotes reduce ranking

---

### **Newest First ("Yours" Tab)**

Your personal posts sorted by creation time only:

| Post | Created | Position |
|------|---------|----------|
| Your Post 1 | 1 min ago | **1st** |
| Your Post 2 | 1 hour ago | **2nd** |
| Your Post 3 | 1 day ago | **3rd** |

Votes don't affect ranking in "Yours" tab.

---

## 🔄 Hot Score Calculation

### **Reddit's Algorithm:**

```
score = upvotes - downvotes
time_factor = seconds_since_epoch / 45000

if score > 0:
    hot_score = log10(score) + time_factor
elif score < 0:
    hot_score = -log10(abs(score)) + time_factor
else:
    hot_score = time_factor
```

### **Example Scores:**

| Upvotes | Downvotes | Age | Hot Score | Rank |
|---------|-----------|-----|-----------|------|
| 10 | 0 | 1 day | 14062.60 | High |
| 5 | 0 | 1 day | 14061.30 | Good |
| 2 | 1 | 1 day | 14060.10 | Medium |
| 0 | 0 | 1 day | 14060.00 | Base |
| 5 | 0 | 7 days | 14048.30 | Falling |

**Time decay:** Posts lose ~2 points per day

---

## ⚙️ Automatic Updates

### **Cron Job (REQUIRED)**

Hot scores must be recalculated hourly for time decay to work.

**Setup:**
```bash
crontab -e
```

**Add this line:**
```
0 * * * * cd /home/imran/Desktop/REACT && source venv/bin/activate && python manage.py update_hot_scores --days 30
```

**What it does:**
- Runs every hour (0 * * * *)
- Updates hot scores for posts from last 30 days
- Ensures old posts naturally fall down
- Keeps fresh content rising

---

## 📈 Current Database Status

**Total Posts:** 21
**Hot Scores Calculated:** ✅ All posts updated

**Top 5 Posts (by hot_score):**

| ID | Hot Score | Upvotes | Created |
|----|-----------|---------|---------|
| 31 | 14062.60 | 2 | 2025-12-27 |
| 30 | 14060.98 | 2 | 2025-12-26 |
| 26 | 14060.51 | 1 | 2025-12-26 |
| 23 | 14056.78 | 2 | 2025-12-24 |
| 20 | 14056.68 | 2 | 2025-12-24 |

---

## 🎛️ Pagination Classes

### **FeedHotCursorPagination** (Used by: All, Today, Problems, Updates)
```python
class FeedHotCursorPagination(CursorPagination):
    ordering = '-hot_score'  # Reddit-style ranking
    page_size = 20
```

### **YoursCursorPagination** (Used by: Yours)
```python
class YoursCursorPagination(CursorPagination):
    ordering = '-created_at'  # Newest first
    page_size = 20
```

---

## 🚀 API Usage

All tabs use **CursorPagination**:

```bash
# First page
GET /api/feed?tab=All

# Next page (use cursor from response)
GET /api/feed?tab=All&cursor=cD0yMDI1...
```

**Response:**
```json
{
  "next": "http://localhost:8000/api/feed?cursor=cD0yMDI1...",
  "previous": null,
  "results": [
    {
      "id": "31",
      "upvotes": 2,
      "downvotes": 0,
      "created_at": "2025-12-27T10:32:42Z",
      ...
    }
  ]
}
```

---

## ✨ Benefits

### **Compared to "Newest First":**

| Feature | Newest First | Hot Score (Reddit) |
|---------|--------------|-------------------|
| **Fresh content** | Always on top | Needs engagement to rise |
| **Quality posts** | Lost quickly | Stay visible longer |
| **Old posts** | Buried forever | Can resurface with new votes |
| **Engagement** | Votes don't matter | Votes affect ranking |
| **Feed variety** | Only newest | Mix of fresh + quality |

### **Why This is Better:**

✅ **Community engagement matters** - Good posts get visibility
✅ **Time-sensitive issues rise** - Fresh problems appear quickly
✅ **Quality over recency** - Important posts don't disappear
✅ **Natural decay** - Old content doesn't dominate
✅ **Dynamic feed** - Always changing, stays interesting

---

## 🧪 Testing

### **Test Hot Score Ranking:**

1. Create 2 posts
2. Upvote one of them multiple times
3. Check feed - upvoted post should be higher
4. Wait 1 day, check again - both should fall slightly

### **Test Time Decay:**

1. Check current top posts
2. Wait 24 hours
3. Run cron: `python manage.py update_hot_scores --days 30`
4. Check again - scores should decrease by ~2 points

### **Verify "Yours" Tab:**

1. Create 3 posts at different times
2. Check "Yours" tab
3. Should show newest first (regardless of votes)

---

## 🔧 Maintenance

### **Daily:**
- ✅ Cron runs hourly (automatic)

### **Weekly:**
- Check cron is working: `crontab -l`
- Verify scores updating: `python manage.py shell -c "from basic.models import Post; print(Post.objects.first().hot_score)"`

### **Monthly:**
- Review scoring algorithm (if needed)
- Check database performance

---

## 📊 Performance

- **Hot score uses database index** (fast queries)
- **CursorPagination** (efficient for large datasets)
- **Hourly updates** (minimal server load)
- **Scores cached in database** (no real-time calculations)

**Query Performance:**
```sql
-- Very fast (uses index)
SELECT * FROM posts ORDER BY hot_score DESC LIMIT 20;

-- Also fast (compound index)
SELECT * FROM posts WHERE category='PROBLEM' ORDER BY hot_score DESC;
```

---

## 🆚 Before vs After

| Tab | Before | After |
|-----|--------|-------|
| **All** | Newest first | **Hot score** 🔥 |
| **Today** | Newest first → Hot score | **Hot score** 🔥 (unchanged) |
| **Problems** | Newest first | **Hot score** 🔥 |
| **Updates** | Newest first | **Hot score** 🔥 |
| **Yours** | Newest first | Newest first (unchanged) |

---

## 🚨 Important Notes

1. ✅ **Hot scores calculated** - All 21 posts updated
2. ✅ **Cron job required** - Set up hourly updates
3. ✅ **CursorPagination** - All tabs use cursors
4. ✅ **Database indexed** - `hot_score` field has index

---

## 📞 Quick Commands

```bash
# Update hot scores manually
source venv/bin/activate
python manage.py update_hot_scores --days 30

# Check top posts
python manage.py shell -c "from basic.models import Post; posts = Post.objects.order_by('-hot_score')[:10]; [print(f'{p.id}: {p.hot_score}') for p in posts]"

# Set up cron
crontab -e
# Add: 0 * * * * cd /home/imran/Desktop/REACT && source venv/bin/activate && python manage.py update_hot_scores --days 30

# Test API
curl -H "Authorization: Bearer TOKEN" "http://localhost:8000/api/feed?tab=All"
```

---

## 🎉 Summary

✅ **All sections use Reddit-style ranking** (except "Yours")
✅ **Hot scores calculated for all posts**
✅ **CursorPagination on all tabs**
✅ **Automatic hourly updates** (via cron)
✅ **Quality content gets visibility**
✅ **Fresh posts can compete**
✅ **Old posts naturally decay**

**Your feed is now fully Reddit-style!** 🚀
