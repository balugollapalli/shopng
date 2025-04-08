from decimal import Decimal
from django.shortcuts import get_object_or_404
from .models import Product

def cart_processor(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')
    total_items = 0
    
    for product_id, item_data in cart.items():
        try:
            product = Product.objects.select_related('category').get(id=product_id)
            quantity = max(1, int(item_data.get('quantity', 1)))
            price = Decimal(str(item_data.get('price', product.price)))
            subtotal = quantity * price
            total += subtotal
            total_items += quantity
            cart_items.append({'product': product,'quantity': quantity,'price': price,'subtotal': subtotal})
        except Product.DoesNotExist:
            del cart[product_id]
    request.session['cart'] = cart
    request.session.modified = True
    return {
        'cart_items': cart_items,
        'cart_total': total,
        'cart_total_items': total_items,
        'cart_subtotal': total,
        'cart_tax': total * Decimal('0.1'),  
        'cart_total_with_tax': total * Decimal('1.1')
    }
    
def wishlist_count(request):
    try:
        if request.user.is_authenticated:
            count = request.user.wishlist.count() if hasattr(request.user, 'wishlist') else 0
            print(f"Wishlist count for {request.user.username}: {count}")
            return {'wishlist_count': count}
    except Exception as e:
        print(f"Error in wishlist_count context processor: {e}")
    
    return {'wishlist_count': 0}