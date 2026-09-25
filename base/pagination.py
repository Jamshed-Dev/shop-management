from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class DefaultPagination(PageNumberPagination):
    page_size = 24
    # Default page size
    
    def get_paginated_response(self, data):
        return Response({
            "meta": {
                "limit": self.get_page_size(self.request),  # Correct page size
                "page": self.page.number,  # Current page number
                "total": self.page.paginator.count,  # Total number of items
                "amount": len(data), 
            },
            "data": data  # Serialized data
        })

class OrderPagination(PageNumberPagination):
    page_size = 100  # Default page size
    
    def get_paginated_response(self, data):
        return Response({
            "meta": {
                "limit": self.get_page_size(self.request),  # Correct page size
                "page": self.page.number,  # Current page number
                "total": self.page.paginator.count,  # Total number of items
            },
            "data": data  # Serialized data
        })

