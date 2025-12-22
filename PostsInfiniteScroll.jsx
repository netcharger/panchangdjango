import React, { useState, useEffect, useCallback, useRef } from 'react';

const PostsInfiniteScroll = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  const observerTarget = useRef(null);

  const API_BASE_URL = 'http://127.0.0.1:8000/api/posts/posts/';

  const fetchPosts = useCallback(async (pageNum) => {
    if (loading) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}?page=${pageNum}`);
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        setPosts(prevPosts => [...prevPosts, ...data.results]);
        setHasMore(!!data.next); // Check if there's a next page
      } else {
        setHasMore(false);
      }
    } catch (error) {
      console.error('Error fetching posts:', error);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [loading]);

  useEffect(() => {
    fetchPosts(1);
  }, []); // Fetch first page on mount

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          const nextPage = page + 1;
          setPage(nextPage);
          fetchPosts(nextPage);
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [hasMore, loading, page, fetchPosts]);

  return (
    <div className="posts-container">
      <div className="posts-grid">
        {posts.map((post) => (
          <div key={post.id} className="post-card">
            {post.featured_image && (
              <div className="post-image">
                <img src={post.featured_image} alt={post.title} />
              </div>
            )}
            <div className="post-content">
              {post.category && (
                <span className="post-category">
                  📁 {post.category.name}
                </span>
              )}
              <h3 className="post-title">{post.title}</h3>
            </div>
          </div>
        ))}
      </div>

      {/* Loading indicator and observer target */}
      <div ref={observerTarget} className="observer-target">
        {loading && (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading more posts...</p>
          </div>
        )}
        {!hasMore && posts.length > 0 && (
          <div className="end-message">
            <p>No more posts to load</p>
          </div>
        )}
      </div>

      <style jsx>{`
        .posts-container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }

        .posts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 24px;
          margin-bottom: 40px;
        }

        .post-card {
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          cursor: pointer;
        }

        .post-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
        }

        .post-image {
          width: 100%;
          height: 200px;
          overflow: hidden;
        }

        .post-image img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: transform 0.5s ease;
        }

        .post-card:hover .post-image img {
          transform: scale(1.05);
        }

        .post-content {
          padding: 20px;
        }

        .post-category {
          display: inline-block;
          background: #f3f4f6;
          color: #6b7280;
          padding: 4px 12px;
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 500;
          margin-bottom: 12px;
        }

        .post-title {
          font-size: 1.1rem;
          font-weight: 600;
          color: #1f2937;
          line-height: 1.5;
          margin: 0;
        }

        .observer-target {
          min-height: 100px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .loading-spinner {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          padding: 40px;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #667eea;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .loading-spinner p {
          color: #6b7280;
          font-size: 0.875rem;
        }

        .end-message {
          text-align: center;
          padding: 40px;
          color: #9ca3af;
          font-size: 0.875rem;
        }
      `}</style>
    </div>
  );
};

export default PostsInfiniteScroll;

