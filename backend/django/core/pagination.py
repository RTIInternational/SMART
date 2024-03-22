from rest_framework.pagination import PageNumberPagination


class LabelViewPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    page_size = 5
    max_page_size = 100


class SmartPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 1000
