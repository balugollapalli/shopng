"""
URL configuration for shopng2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from store import views as store_views  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  
    path('', include('store.urls')),
    path('providers/',include('providers.urls')),
    path('', store_views.home, name='home'),  
]

if settings.DEBUG:  # Serve media files only in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
handler404 = 'store.views.custom_404_view'
handler500 = 'store.views.custom_500_view'
