"""
Pagination classes for Audio Manager API
"""
from rest_framework.pagination import PageNumberPagination


class AudioFilePagination(PageNumberPagination):
    """
    Custom pagination for audio files.
    Returns 10 items per page.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

