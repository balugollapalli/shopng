from django import template
from ..models import Category, Product, Wishlist, Brand  
from decimal import Decimal
from django.forms.boundfield import BoundField
from django.db.models import Avg, Count, Q
from django.utils.text import slugify

register = template.Library()

@register.simple_tag(takes_context=True)
def get_categories(context):
    request = context.get('request')
    categories = Category.objects.all()
    current_category = request.GET.get('category') if request else None  
    for category in categories:
        category.is_selected = (current_category == category.slug)
    return categories

@register.simple_tag
def get_popular_products(count=5):
    return Product.objects.filter(available=True).order_by('-created')[:count]


@register.filter
def currency(value):
    try:
        return f"${float(value):.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter
def is_in_wishlist(product, user):
    if not user or not user.is_authenticated:
        return False
    return Wishlist.objects.filter(user=user, product=product).exists()

@register.filter
def sub(value, arg):
    try:
        return Decimal(value) - Decimal(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def percentage(value, total):
    try:
        return round((Decimal(value) / Decimal(total)) * 100, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.simple_tag
def get_related_products(product, limit=4):
    return Product.objects.filter(category=product.category, available=True).exclude(id=product.id)[:limit]

@register.simple_tag
def get_brand_products(brand, limit=4):
    return Product.objects.filter(brand=brand, available=True)[:limit]

@register.filter
def stock_percentage(product):
    try:
        total_stock = product.stock
        available_stock = product.stock
        return round((available_stock / total_stock) * 100, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    try:
        return Decimal(value) * Decimal(arg)
    except (ValueError, TypeError):
        return ''



