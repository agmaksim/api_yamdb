from rest_framework.pagination import PageNumberPagination


class YamdbPagination(PageNumberPagination):
    page_size = 10
