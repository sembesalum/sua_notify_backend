from django.contrib import admin
from django.urls import path, include

from university_admin.views import AdminDashboard

urlpatterns = [
    path('', AdminDashboard.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('university_admin.urls')),  # Changed from university_admin/ to api/
]