/**
 * Custom React Hook for Infinite Scrolling Posts
 * Usage: const { posts, loading, hasMore, error } = useInfinitePosts();
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const useInfinitePosts = (apiUrl = 'http://127.0.0.1:8000/api/posts/posts/') => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);
  const observerTarget = useRef(null);

  const fetchPosts = useCallback(async (pageNum) => {
    if (loading) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${apiUrl}?page=${pageNum}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        setPosts(prevPosts => [...prevPosts, ...data.results]);
        setHasMore(!!data.next); // Check if there's a next page URL
      } else {
        setHasMore(false);
      }
    } catch (err) {
      console.error('Error fetching posts:', err);
      setError(err.message);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [loading, apiUrl]);

  // Fetch first page on mount
  useEffect(() => {
    fetchPosts(1);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Set up intersection observer for infinite scroll
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

  // Reset function to start fresh
  const reset = useCallback(() => {
    setPosts([]);
    setPage(1);
    setHasMore(true);
    setError(null);
    fetchPosts(1);
  }, [fetchPosts]);

  return {
    posts,
    loading,
    hasMore,
    error,
    observerTarget,
    reset
  };
};

export default useInfinitePosts;

