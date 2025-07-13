
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Quyền tùy chỉnh để chỉ cho phép chủ sở hữu của một đối tượng có thể chỉnh sửa nó.
    """
    def has_object_permission(self, request, view, obj):
        # Quyền đọc được cho phép cho mọi request,
        # vì vậy chúng ta sẽ luôn cho phép các request GET, HEAD hoặc OPTIONS.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Quyền ghi chỉ được phép cho chủ sở hữu của đối tượng.
        return obj.author == request.user

class IsAdminUser(permissions.BasePermission):
    """
    Quyền tùy chỉnh để chỉ cho phép admin (staff users) truy cập.
    """
    def has_permission(self, request, view):
        # Chỉ trả về True nếu user đã đăng nhập và là staff.
        return request.user and request.user.is_authenticated and request.user.is_staff
