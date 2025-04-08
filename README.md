# 🛍️ Shopng - Django E-commerce Web App

Shopng is a modern, feature-rich e-commerce web application built with Django. It supports user and vendor logins, product advertisements, dynamic UI, order management, and much more — all while following a clean modular project structure.

---

## 🚀 Features

- 🔐 **User Authentication**: Step-by-step sign-up with OTP login
- 🛍️ **Products & Categories**: Organized products with brand & category filtering
- 🏷️ **Vendor Portal**: Vendors can create product advertisements and discounts
- 💼 **Cart & Orders**: Cart system, order placement, and tracking
- ❤️ **Wishlist**: Add favorite items to wishlist
- 📧 **Email Support**: Gmail-based OTP and notifications
- 🖼️ **Media Uploads**: Handles product images and user uploads
- 🧠 **Custom Template Tags & Filters**
- 🎨 **Reusable & Responsive Templates**

---

## 🗂️ Project Structure

shopng/  (Your main project directory)
├── accounts/
│   ├── migrations/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── tokens.py
│   ├── backends.py
│   └── __init__.py
├── providers/
│   ├── migrations/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── __init__.py
├── store/
│   ├── migrations/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── templatetags/
│   │   ├── form_tags.py
│   │   ├── math_filters.py
│   │   ├── store_tags.py
│   │   └── wishlist_tags.py
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── email_username_auth.py  
│   └── __init__.py
├── shopng/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── __init__.py
├── manage.py
├── db.sqlite3
├── static/
│   └── ... (your static files)
├── media/
│   └── ... (your media files)
└── templates/
│   │   ├── accounts/ 
│   │   └──includes
│   │   ├── providers/
│   │   ├── registration/  
│   │   └── store/ 
    └── base.html      



---

## ⚙️ Getting Started

### 🔧 Prerequisites
- Python 3.10+
- pip
- Git

### 🔍 Clone the Repository
