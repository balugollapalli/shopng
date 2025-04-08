from django.urls import path
from . import views

app_name = 'providers'

urlpatterns = [
    path('', views.vendor_dashboard, name='vendor_dashboard'),
    
    path('login/', views.vendor_login, name='vendor_login'),
    path('register/', views.vendor_register, name='vendor_register'),
    path('logout/', views.vendor_logout, name='vendor_logout'),
    # Brand URLs
    path('brands/', views.vendor_brand_list, name='vendor_brand_list'),
    path('brands/create/', views.vendor_brand_create, name='vendor_brand_create'),
    path('brands/<int:pk>/edit/', views.vendor_brand_update, name='vendor_brand_update'),
    path('brands/<int:pk>/delete/', views.vendor_brand_delete, name='vendor_brand_delete'),

    # Category URLs
    path('categories/', views.vendor_category_list, name='vendor_category_list'),
    path('categories/create/', views.vendor_category_create, name='vendor_category_create'),
    path('categories/<int:pk>/edit/', views.vendor_category_update, name='vendor_category_update'),
    path('categories/<int:pk>/delete/', views.vendor_category_delete, name='vendor_category_delete'),

    # Product URLs
    path('products/', views.vendor_product_list, name='vendor_product_list'),
    path('products/create/', views.vendor_product_create, name='vendor_product_create'),
    path('products/<int:pk>/edit/', views.vendor_product_update, name='vendor_product_update'),
    path('products/<int:pk>/delete/', views.vendor_product_delete, name='vendor_product_delete'),
    # Update these URL patterns in urls.py
    path('products/<int:product_pk>/variations/', views.vendor_variation_list, name='vendor_variation_list'),
    path('products/<int:product_pk>/variations/create/', views.vendor_variation_create, name='vendor_variation_create'),
    path('products/<int:product_pk>/variations/<int:pk>/edit/', views.vendor_variation_update, name='vendor_variation_update'),
    path('products/<int:product_pk>/variations/<int:pk>/delete/', views.vendor_variation_delete, name='vendor_variation_delete'),
    
    #static
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('terms/', views.terms, name='terms'),
]
