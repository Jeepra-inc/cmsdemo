# pagination.py
from rest_framework.pagination import PageNumberPagination

class FormPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'  # Allow clients to override `page_size`
    max_page_size = 100  # Set a max limit for `page_size`
