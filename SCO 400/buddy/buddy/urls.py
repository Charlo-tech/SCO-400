from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('website.urls')),
]


admin.site.site_header = "Buddy Admin Site"
admin.site.site_title = "BuddySystem"
admin.site.index_title = "Welcome to Buddy System"