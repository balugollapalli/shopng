# store/views.py
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Q, F, Avg, Count, Min, Max
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from .models import *
from .forms import *
from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import Lower
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.db import transaction
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)

def home(request):
    products = Product.objects.filter(available=True).annotate(
        discount_amount=F('original_price') - F('price')
    )[:8]
    categories = Category.objects.all()[:6]
    featured_brands = Brand.objects.annotate(num_products=Count('products')).filter(num_products__gt=0)[:6]
    return render(request, 'store/home.html', {
        'products': products,
        'categories': categories,
        'featured_brands': featured_brands,
        'wishlist_count': request.user.wishlist.count() if request.user.is_authenticated else 0
    })

def search_products(request):
    form = ProductSearchForm(request.GET or None)
    products = Product.objects.filter(available=True)
    context = {'form': form,'products': [],'categories': Category.objects.all(),'brands': Brand.objects.all(),}
    if request.GET:
        query = request.GET.get('query', '').strip()
        category_id = request.GET.get('category', '')
        brand_id = request.GET.get('brand', '')
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        sort_by = request.GET.get('sort_by', 'name')
        if query:
            products = products.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(brand__name__icontains=query))
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                products = products.filter(category=category)
                context['selected_category'] = category
            except Category.DoesNotExist:
                pass
        if brand_id:
            try:
                brand = Brand.objects.get(id=brand_id)
                products = products.filter(brand=brand)
                context['selected_brand'] = brand
            except Brand.DoesNotExist:
                pass
        if min_price:
            try:
                products = products.filter(price__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                products = products.filter(price__lte=Decimal(max_price))
            except (ValueError, TypeError):
                pass
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created')
        elif sort_by == 'name':
            products = products.order_by(Lower('name'))
        paginator = Paginator(products, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context.update({'products': page_obj,'page_obj': page_obj,'is_paginated': page_obj.has_other_pages(),'current_query': query,'current_min_price': min_price,'current_max_price': max_price,'sort_by': sort_by})
    return render(request, 'store/search_results.html', context)

def brand_list(request):
    brands = Brand.objects.all()
    return render(request, 'store/brand_list.html', {'brands': brands})

def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    products = brand.products.filter(available=True)
    return render(request, 'store/brand_detail.html', {'brand': brand,'products': products})

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'store/category_list.html', {'categories': categories})

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(available=True)
    brands = category.brands.all()
    return render(request, 'store/category_detail.html', {'category': category,'products': products,'brands': brands})

def product_list(request, category_slug=None):
    products = Product.objects.all()
    categories = Category.objects.all()
    brands = Brand.objects.all()
    breadcrumbs = [
        {'name': 'Home', 'url': reverse('store:home')},
        {'name': 'All Products', 'url': reverse('store:product_list')}
    ]
    query = request.GET.get('query', '').strip()
    category_filter = request.GET.get('category', '')
    brand_filter = request.GET.get('brand', '')
    min_price = request.GET.get('min_price')  
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort', '')
    if query:
        products = products.search(query)
    if category_filter:
        try:
            category = Category.objects.get(slug=category_filter)
            products = products.filter(category=category)
            breadcrumbs.append({'name': category.name, 'url': None})
        except Category.DoesNotExist:
            pass
    if brand_filter:
        try:
            brand = Brand.objects.get(id=brand_filter)
            products = products.filter(brand=brand)
        except Brand.DoesNotExist:
            pass
    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except (ValueError, TypeError):
            pass
    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except (ValueError, TypeError):
            pass
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created')
    elif sort == 'name':
        products = products.order_by(Lower('name'))
    products = products.available()
    paginator = Paginator(products, 12)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    cart = request.session.get('cart', {})
    cart_product_ids = {int(key.split('-')[0]) for key in cart.keys()}
    context = {'products': page_obj,'categories': categories,'brands': brands,'page_obj': page_obj,'is_paginated': page_obj.has_other_pages(),'current_sort': sort,'current_query': query,'current_category': category_filter,'current_min_price': min_price,'current_max_price': max_price,'current_brand': brand_filter,
               'breadcrumbs': breadcrumbs,'cart_product_ids': cart_product_ids,}
    return render(request, 'store/product_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    rating_distribution = product.rating_distribution() if reviews.exists() else {
        5: {'count': 0, 'percentage': 0},
        4: {'count': 0, 'percentage': 0},
        3: {'count': 0, 'percentage': 0},
        2: {'count': 0, 'percentage': 0},
        1: {'count': 0, 'percentage': 0}
    }
    cart = request.session.get('cart', {})
    in_cart = False
    for key in cart.keys():
        if str(product.id) == key.split('-')[0]:
            in_cart = True
            break
    context = {'product': product,'reviews': reviews,'average_rating': average_rating,'total_reviews': reviews.count(),
               'rating_distribution': rating_distribution,'in_cart': in_cart }
    return render(request, 'store/product_detail.html', context)

def toggle_wishlist(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
        if wishlist_item:
            wishlist_item.delete()
            return JsonResponse({'success': True, 'message': 'Removed from wishlist','in_wishlist': False})
        else:
            Wishlist.objects.create(user=request.user, product=product)
            return JsonResponse({'success': True, 'message': 'Added to wishlist','in_wishlist': True})
    else:
        return JsonResponse({'success': False, 'message': 'Please log in to add to wishlist.'})

def wishlist_view(request):
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user)
        return render(request, 'store/wishlist.html', {'wishlist_items': wishlist_items})
    else:
        messages.info(request, "Please log in to view your wishlist.") 
        return redirect('accounts:login') 

@login_required
def wishlist_count(request):
    if request.user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        return JsonResponse({'count': wishlist_count})
    else:
        return JsonResponse({'count': 0})

def move_to_cart(request, wishlist_item_id):
    if request.user.is_authenticated:
        wishlist_item = get_object_or_404(Wishlist, id=wishlist_item_id, user=request.user)
        cart = request.session.get('cart', {})
        product = wishlist_item.product
        cart[str(product.id)] = {'quantity': 1,'price': float(product.price)}
        request.session['cart'] = cart
        wishlist_item.delete()
        messages.success(request, f'{product.name} moved to cart from wishlist')
        return redirect('store:wishlist')
    else:
        messages.info(request, "Please log in to move items to your cart.")
        return redirect('accounts:login')

def cart_add(request, product_id, variation_id=None):
    try:
        product = get_object_or_404(Product, id=product_id)
        cart = request.session.get('cart', {})
        if request.method == 'POST':
            body = json.loads(request.body) if request.body else {}
            quantity = int(body.get('quantity', 1))
            variation_id = body.get('variation_id', variation_id)
        else:
            quantity = int(request.GET.get('quantity', 1))
            variation_id = request.GET.get('variation_id', variation_id)
        variation = None
        if variation_id:
            variation = get_object_or_404(ProductVariation, id=variation_id, product=product)
        cart_item_key = f"{product_id}"
        if variation:
            cart_item_key = f"{product_id}-{variation_id}"
        available_stock = variation.stock if variation else product.stock
        if quantity > available_stock:
            return JsonResponse({'success': False,'message': f'Only {available_stock} items available in stock'}, status=400)
        item_price = variation.price if variation else product.price
        if cart_item_key in cart:
            cart[cart_item_key]['quantity'] = min(cart[cart_item_key]['quantity'] + quantity, available_stock)
        else:
            cart[cart_item_key] = {'quantity': quantity,'price': float(item_price),'name': product.name,'image': product.image.url if product.image else '','slug': product.slug,'product_id': product_id}
            if variation:
                cart[cart_item_key].update({'variation_id': variation.id,'variation_name': variation.name,'variation_value': variation.value})
        request.session['cart'] = cart
        request.session.modified = True
        total_items = sum(item['quantity'] for item in cart.values())
        total_cost = sum(Decimal(str(item['price'])) * item['quantity'] for item in cart.values())
        response_data = {'success': True,'message': f"{product.name} added to cart",'cart_total': float(total_cost),'cart_total_items': total_items,'redirect': request.GET.get('redirect', 'false')}
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
        
@require_POST
def cart_remove(request, product_id, variation_id=None):
    try:
        cart = request.session.get('cart', {})
        cart_item_key = f"{product_id}"
        if variation_id:
            cart_item_key = f"{product_id}-{variation_id}"
        elif request.GET.get('variation_id'):
            cart_item_key = f"{product_id}-{request.GET.get('variation_id')}"
        elif request.body:
            body = json.loads(request.body)
            if body.get('variation_id'):
                cart_item_key = f"{product_id}-{body.get('variation_id')}"
        if cart_item_key in cart:
            del cart[cart_item_key]
        request.session['cart'] = cart
        request.session.modified = True
        total_items = sum(item['quantity'] for item in cart.values())
        total_cost = sum(Decimal(str(item['price'])) * item['quantity'] for item in cart.values())
        return JsonResponse({'success': True,'cart_total': float(total_cost),'cart_total_items': total_items})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')
    for cart_item_key, item_data in cart.items():
        try:
            if '-' in cart_item_key:
                product_id, variation_id = cart_item_key.split('-')
            else:
                product_id, variation_id = cart_item_key, None
            product = Product.objects.get(id=product_id)
            quantity = int(item_data['quantity'])
            price = Decimal(str(item_data['price']))
            subtotal = quantity * price
            total += subtotal
            cart_item = {'product': product,'quantity': quantity,'price': price,'subtotal': subtotal,'cart_item_key': cart_item_key}
            if variation_id:
                try:
                    variation = ProductVariation.objects.get(id=variation_id, product=product)
                    cart_item['variation'] = variation
                except ProductVariation.DoesNotExist:
                    pass
            cart_items.append(cart_item)
        except Product.DoesNotExist:
            del cart[cart_item_key]
    request.session['cart'] = cart
    request.session.modified = True
    return render(request, 'store/cart.html', {'cart_items': cart_items,'cart_total': total,'subtotal': total,'tax': total * Decimal('0.1'),'total_with_tax': total * Decimal('1.1')})

def cart_status(request):
    cart = request.session.get('cart', {})
    total_items = sum(item['quantity'] for item in cart.values())
    total_cost = sum(Decimal(str(item['price'])) * item['quantity'] for item in cart.values())
    return JsonResponse({'total_items': total_items,'total_cost': float(total_cost)})

def cart_update(request):
    try:
        data = json.loads(request.body)
        cart_item_key = data.get('cart_item_key')
        quantity = data.get('quantity')
        if not cart_item_key and data.get('product_id'):
            product_id = data.get('product_id')
            variation_id = data.get('variation_id')
            cart_item_key = f"{product_id}-{variation_id}" if variation_id else f"{product_id}"
        if not cart_item_key or not quantity:
            return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
        cart = request.session.get('cart', {})
        if cart_item_key in cart:
            if '-' in cart_item_key:
                product_id, variation_id = cart_item_key.split('-')
                product = get_object_or_404(Product, id=product_id)
                variation = get_object_or_404(ProductVariation, id=variation_id, product=product)
                available_stock = variation.stock
            else:
                product_id = cart_item_key
                product = get_object_or_404(Product, id=product_id)
                available_stock = product.stock
            if quantity > available_stock:
                return JsonResponse({'success': False, 'message': f'Only {available_stock} items available in stock'}, status=400)
            cart[cart_item_key]['quantity'] = quantity
            request.session['cart'] = cart
            request.session.modified = True
        total_items = sum(item['quantity'] for item in cart.values())
        total_cost = sum(
            Decimal(str(item['price'])) * item['quantity'] 
            for item in cart.values()
        )
        return JsonResponse({'success': True,'quantity': quantity,'cart_total': float(total_cost),'cart_total_items': total_items})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Your cart is empty")
        return redirect('store:cart')

    cart_items = []
    subtotal = Decimal('0.00')

    for cart_item_key, item_data in cart.items():
        try:
            if '-' in cart_item_key:
                product_id, variation_id = cart_item_key.split('-')
            else:
                product_id, variation_id = cart_item_key, None

            product = Product.objects.get(id=product_id)
            quantity = int(item_data['quantity'])
            price = Decimal(str(item_data['price']))
            item_total = quantity * price
            subtotal += item_total

            cart_item = {
                'product': product,
                'quantity': quantity,
                'price': price,
                'subtotal': item_total,
                'cart_item_key': cart_item_key
            }

            if variation_id:
                try:
                    variation = ProductVariation.objects.get(id=variation_id, product=product)
                    cart_item['variation'] = variation
                except ProductVariation.DoesNotExist:
                    pass

            cart_items.append(cart_item)
        except Product.DoesNotExist:
            del cart[cart_item_key]

    request.session['cart'] = cart
    request.session.modified = True

    tax = subtotal * Decimal('0.10')
    total_with_tax = subtotal + tax

    addresses = UserAddress.objects.filter(user=request.user)
    address_form = UserAddressForm()

    if request.method == 'POST':
        if 'name' in request.POST:
            address_form = UserAddressForm(request.POST)
            if address_form.is_valid():
                try:
                    existing_address = UserAddress.objects.filter(
                        user=request.user,
                        street_address=address_form.cleaned_data['street_address'],
                        city=address_form.cleaned_data['city'],
                        state=address_form.cleaned_data['state'],
                        postal_code=address_form.cleaned_data['postal_code']
                    ).first()

                    shipping_address = existing_address or address_form.save(commit=False)
                    shipping_address.user = request.user
                    shipping_address.save()

                    messages.success(request, 'Address added successfully')
                    return redirect('store:checkout')

                except Exception as e:
                    messages.error(request, f"Error adding address: {str(e)}")
                    return redirect('store:checkout')
            else:
                messages.error(request, "Invalid address details")
                return redirect('store:checkout')

        address_id = request.POST.get('selected_address')
        if address_id:
            try:
                shipping_address = UserAddress.objects.get(id=address_id, user=request.user)
                name_parts = shipping_address.name.split()
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

                order = Order.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=request.user.email,
                    address=shipping_address.street_address,
                    city=shipping_address.city,
                    state=shipping_address.state,
                    postal_code=shipping_address.postal_code,
                    country=shipping_address.country,
                    phone=shipping_address.phone_number or '',
                    total=total_with_tax,
                    status='pending'
                )

                for cart_item in cart_items:
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=cart_item['product'],
                        price=cart_item['price'],
                        quantity=cart_item['quantity']
                    )
                    if 'variation' in cart_item:
                        order_item.variation = cart_item['variation']
                        order_item.variation_name = cart_item['variation'].name
                        order_item.variation_value = cart_item['variation'].value
                        order_item.save()

                try:
                    user_email = order.user.email if order.user else order.email
                    context = {
                        'order': order,
                        'order_items': order.items.all(),
                        'shipping_address': shipping_address,
                        'payment_url': request.build_absolute_uri(f'/orders/{order.id}/pay/?from_email=true'),
                        'subtotal': subtotal,
                        'tax': tax,
                        'grand_total': total_with_tax
                    }

                    html_message = render_to_string('store/order_invoice.html', context)
                    plain_message = strip_tags(html_message)

                    send_mail(
                        subject=f'Order Confirmation - Invoice #{order.id}',
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user_email],
                        html_message=html_message,
                        fail_silently=False,
                    )

                except Exception as e:
                    print("Email send error:", str(e))

                request.session['cart'] = {}
                request.session.modified = True
                messages.success(request, 'Order placed successfully!')
                return redirect('store:order_confirmation', order_id=order.id)

            except UserAddress.DoesNotExist:
                messages.error(request, 'Invalid address selected')
        else:
            messages.error(request, 'Please select a shipping address')

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'total_with_tax': total_with_tax,
        'addresses': addresses,
        'address_form': address_form
    })



@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})

@login_required
def manage_addresses(request):
    addresses = UserAddress.objects.filter(user=request.user)
    if request.method == 'POST':
        form = UserAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if form.cleaned_data.get('is_default'):
                UserAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
            address.save()
            messages.success(request, 'Address added successfully')
            return redirect('store:manage_addresses')
        else:
            for field, errors in form.errors.items():
                messages.error(request, f"{field}: {errors}")
    else:
        form = UserAddressForm()
    return render(request, 'store/manage_addresses.html', {'addresses': addresses,'form': form})
    
@login_required
def set_default_address(request, address_id):
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    UserAddress.objects.filter(user=request.user).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, 'Default address updated successfully')
    return redirect('store:manage_addresses')

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    if address.is_default:
        messages.error(request, 'Cannot delete default address')
    else:
        address.delete()
        messages.success(request, 'Address deleted successfully')
    return redirect('store:manage_addresses')

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    if request.method == 'POST':
        form = UserAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully')
            return redirect('store:manage_addresses')
    else:
        form = UserAddressForm(instance=address)
    return render(request, 'store/edit_address.html', {
        'form': form,
        'address': address
    })
    

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'store/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    tracking_steps = ["Order Placed", "Payment Done", "Processing", "Shipped", "Delivered"]

    return render(request, 'store/order_detail.html', {'order': order,'order_items': order_items,'tracking_steps': tracking_steps})

@login_required
def order_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.paid:
        messages.info(request, 'This order is already paid.')
        return redirect('store:order_detail', order_id=order.id)

    if request.method == 'POST':
        # simulate payment success here
        try:
            with transaction.atomic():
                order.paid = True
                order.status = 'processing'
                order.transaction_id = f"TXN-{order.id}-{timezone.now().timestamp()}"
                order.save()

                # Reduce stock
                for item in order.items.all():
                    product = item.product
                    if item.variation:
                        variation = item.variation
                        if variation.stock >= item.quantity:
                            variation.stock -= item.quantity
                            variation.save()
                        else:
                            raise Exception(f"Not enough stock for {variation.name} ({variation.value})")
                    else:
                        if product.stock >= item.quantity:
                            product.stock -= item.quantity
                            product.save()
                        else:
                            raise Exception(f"Not enough stock for {product.name}")

                messages.success(request, "Payment successful! Order is now processing.")
                return redirect('store:order_detail', order_id=order.id)

        except Exception as e:
            messages.error(request, f"Payment failed: {str(e)}")
            return redirect('store:order_payment', order_id=order.id)

    return render(request, 'store/order_payment.html', {'order': order})

@login_required
def submit_review(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        order_id = request.POST.get('order_id')
        rating = request.POST.get('rating')
        review_text = request.POST.get('review')
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            product = Product.objects.get(id=product_id)
            existing_review = Review.objects.filter(user=request.user, product=product, order=order).exists()
            if existing_review:
                return JsonResponse({'success': False, 'message': 'You have already reviewed this product.'})
            Review.objects.create(user=request.user,product=product,order=order,rating=rating,review_text=review_text)
            return JsonResponse({'success': True})
        except (Order.DoesNotExist, Product.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Invalid product or order.'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def custom_404_view(request, exception):
    return redirect('store:home')  

def custom_500_view(request):
    return redirect('store:home')

