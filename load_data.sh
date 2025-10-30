#!/bin/bash
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata User.json UserProfile.json UserAddress.json CustomUserManager.json \
Brand.json Category.json ProductManager.json ProductQuerySet.json ProductVariation.json Product.json \
Order.json OrderItem.json Review.json Wishlist.json \
VendorUser.json VendorUserManager.json Vendor.json VendorBrand.json VendorCategory.json VendorProduct.json
