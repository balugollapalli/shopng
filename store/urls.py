from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),

    # Product URLs
    path('products/', views.product_list, name='product_list'),
    path('products/category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search_products, name='search_products'),  # Named URL for search

    # Brand URLs
    path('brands/', views.brand_list, name='brand_list'),
    path('brand/<slug:slug>/', views.brand_detail, name='brand_detail'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    # Wishlist URLs
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/move-to-cart/<int:wishlist_item_id>/', views.move_to_cart, name='move_to_cart'),
    path('wishlist/count/', views.wishlist_count, name='wishlist_count'),

    # Cart URLs
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/add/<int:product_id>/<int:variation_id>/', views.cart_add, name='cart_add_with_variation'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/remove/<int:product_id>/<int:variation_id>/', views.cart_remove, name='cart_remove_with_variation'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/status/', views.cart_status, name='cart_status'),

    # Checkout and Order URLs
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('orders/', views.order_history, name='order_history'),  # Order history
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),  # Order detail
    path('orders/<int:order_id>/pay/', views.order_payment, name='order_payment'),

    # Address URLs
    path('addresses/', views.manage_addresses, name='manage_addresses'),
    path('addresses/set-default/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('addresses/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('addresses/delete/<int:address_id>/', views.delete_address, name='delete_address'),
]
