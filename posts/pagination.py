from rest_framework.pagination import PageNumberPagination


class PostPagination(PageNumberPagination):
    """Custom pagination for posts - 10 items per page"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

