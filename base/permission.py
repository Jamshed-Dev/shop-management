from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS



class IsAdminOrReadOnly(permissions.BasePermission): # this is a custom permission class for admin only
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
    
class FullDjangoModelPermissions(permissions.DjangoModelPermissions):
    def __init__(self) -> None:
        self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']

class ViewCustomerHistoryPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('store.view_history')
    
class IsAuthenticatedOrReadOnly(permissions.BasePermission):


    def has_permission(self, request, view):
        # If the method is safe (GET, HEAD, OPTIONS), allow access
        if request.method in SAFE_METHODS:
            return True

        # If the user is authenticated, allow full access (POST, PUT, DELETE, etc.)
        return request.user and request.user.is_authenticated