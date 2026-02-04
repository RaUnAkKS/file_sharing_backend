from rest_framework.pagination import CursorPagination

class FileCursorPagination(CursorPagination):
    page_size = 6
    ordering = '-uploaded_at'
    cursor_query_param = 'cursor'


