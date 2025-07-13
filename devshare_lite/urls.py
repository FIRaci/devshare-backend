from django.contrib import admin
from django.urls import path, include # Nhớ thêm include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Thêm dòng này:
    # Bất kỳ URL nào bắt đầu bằng 'api/' sẽ được chuyển đến file urls.py của app api
    path('api/', include('api.urls')),
]
