from rest_framework.pagination import CursorPagination

class ShareLinkCursorPagination(CursorPagination):
    page_size = 6
    ordering = '-created_at'
    cursor_query_param = 'cursor'