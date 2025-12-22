# Infinite Scrolling Implementation Guide

## Backend Changes

The posts API endpoint now supports pagination with **10 posts per page**.

### API Response Format

When you call `/api/posts/posts/`, the response will be paginated:

```json
{
  "count": 100,
  "next": "http://127.0.0.1:8000/api/posts/posts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Post Title",
      "slug": "post-slug",
      "featured_image": "http://127.0.0.1:8000/media/posts/image.webp",
      "category": {
        "name": "Category Name",
        "slug": "category-slug"
      }
    },
    ...
  ]
}
```

### Endpoints

- **First page:** `/api/posts/posts/` or `/api/posts/posts/?page=1`
- **Next page:** `/api/posts/posts/?page=2`
- **Custom page size:** `/api/posts/posts/?page=1&page_size=20` (max 100)

## Frontend Implementation

### Option 1: Using the React Component

Import and use the `PostsInfiniteScroll` component:

```jsx
import PostsInfiniteScroll from './PostsInfiniteScroll';

function App() {
  return (
    <div>
      <h1>All Posts</h1>
      <PostsInfiniteScroll />
    </div>
  );
}
```

### Option 2: Using the Custom Hook

Use the `useInfinitePosts` hook for more control:

```jsx
import useInfinitePosts from './PostsInfiniteScrollHook';

function PostsPage() {
  const { posts, loading, hasMore, error, observerTarget } = useInfinitePosts();

  return (
    <div>
      <div className="posts-grid">
        {posts.map((post) => (
          <div key={post.id} className="post-card">
            {post.featured_image && (
              <img src={post.featured_image} alt={post.title} />
            )}
            {post.category && (
              <span className="category">{post.category.name}</span>
            )}
            <h3>{post.title}</h3>
          </div>
        ))}
      </div>

      {/* Observer target for infinite scroll */}
      <div ref={observerTarget}>
        {loading && <p>Loading...</p>}
        {!hasMore && <p>No more posts</p>}
      </div>
    </div>
  );
}
```

### Option 3: Manual Implementation

```javascript
let page = 1;
let loading = false;
let hasMore = true;
const posts = [];

async function loadMorePosts() {
  if (loading || !hasMore) return;
  
  loading = true;
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/posts/posts/?page=${page}`);
    const data = await response.json();
    
    posts.push(...data.results);
    hasMore = !!data.next;
    page++;
    
    // Render posts
    renderPosts();
  } catch (error) {
    console.error('Error:', error);
  } finally {
    loading = false;
  }
}

// Use Intersection Observer to detect when user scrolls near bottom
const observer = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting && hasMore && !loading) {
    loadMorePosts();
  }
});

observer.observe(document.querySelector('#load-more-trigger'));
```

## Notes

- **Page size:** Default is 10 posts per page
- **Category filtering:** When using `?category=slug`, category field is excluded from response
- **Performance:** The API uses `select_related` and `prefetch_related` for optimal database queries
- **CORS:** Already enabled for all origins

## Testing

Test the pagination:

```bash
# First page
curl http://127.0.0.1:8000/api/posts/posts/

# Second page
curl http://127.0.0.1:8000/api/posts/posts/?page=2

# With category filter (no category in response)
curl http://127.0.0.1:8000/api/posts/posts/?category=education-science&page=1
```

