from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_backends
from django.contrib import messages
from django.contrib.auth.models import User
from store.models import *
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from .models import *
from .forms import *


def vendor_required(view_func):
    @login_required(login_url='providers:vendor_login')
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'vendor'):
            return view_func(request, *args, **kwargs)
        return redirect('providers:vendor_login')
    return wrapper

def get_vendor(user):
    try:
        return user.vendor
    except Vendor.DoesNotExist:
        return None

def vendor_register(request):
    breadcrumbs = [
        {'title': 'Register', 'url': None}
    ]
    if request.method == 'POST':
        form = VendorUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create associated Vendor profile
            Vendor.objects.create(user=user, shop_name=form.cleaned_data['shop_name'])
            backend = 'providers.backends.EmailBackend'
            login(request, user,backend=backend)
            messages.success(request, 'Vendor account created successfully.')
            return redirect('providers:vendor_dashboard')
    else:
        form = VendorUserCreationForm()
    return render(request, 'providers/vendor_register.html', {'form': form, 'breadcrumbs': breadcrumbs})

def vendor_login(request):
    breadcrumbs = [
        {'title': 'Login', 'url': None}
    ]
    if request.method == 'POST':
        form = VendorLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, email=email, password=password)
            if user:
                # Force backend (avoid ValueError or fallback to wrong user model)
                user.backend = 'providers.backends.EmailBackend'
                login(request, user)
                return redirect('providers:vendor_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = VendorLoginForm()
    return render(request, 'providers/vendor_login.html', {'form': form, 'breadcrumbs': breadcrumbs})

def vendor_logout(request):
    logout(request)
    return redirect(settings.VENDOR_LOGOUT_REDIRECT_URL)


@vendor_required
def vendor_dashboard(request):
    vendor = Vendor.objects.get(user=request.user)
    breadcrumbs = [
        {'title': 'Dashboard', 'url': None}
    ]
    return render(request, 'providers/dashboard.html', {'vendor': vendor, 'breadcrumbs': breadcrumbs})
# ----------------------------
# BRAND VIEWS
# ----------------------------
@vendor_required
def vendor_brand_list(request):
    vendor = get_vendor(request.user)
    brands = VendorBrand.objects.filter(vendor=vendor)
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Brands', 'url': None}
    ]
    return render(request, 'providers/vendor_brand_list.html', {'brands': brands, 'breadcrumbs': breadcrumbs})
    
@vendor_required
def vendor_brand_create(request):
    vendor = get_vendor(request.user)
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Brands', 'url': reverse('providers:vendor_brand_list')},
        {'title': 'Add Brand', 'url': None}
    ]
    if request.method == 'POST':
        form = VendorBrandForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(vendor=vendor)
            messages.success(request, 'Brand created successfully.')
            return redirect('providers:vendor_brand_list')
    else:
        form = VendorBrandForm()
    return render(request, 'providers/vendor_brand_form.html', {'form': form, 'breadcrumbs': breadcrumbs})

@vendor_required
def vendor_brand_update(request, pk):
    vendor = get_vendor(request.user)
    vendor_brand = get_object_or_404(VendorBrand, pk=pk, vendor=vendor)
    brand = vendor_brand.brand  # ✔️ get the related Brand object
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Brands', 'url': reverse('providers:vendor_brand_list')},
        {'title': f'Edit {brand.name}', 'url': None}
    ]
    if request.method == 'POST':
        form = VendorBrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            form.save(vendor=vendor)
            messages.success(request, 'Brand updated successfully.')
            return redirect('providers:vendor_brand_list')
    else:
        form = VendorBrandForm(instance=brand)
    return render(request, 'providers/vendor_brand_form.html', {'form': form, 'breadcrumbs': breadcrumbs})

@vendor_required
def vendor_brand_delete(request, pk):
    vendor = get_vendor(request.user)
    vendor_brand = get_object_or_404(VendorBrand, pk=pk, vendor=vendor)
    brand = vendor_brand.brand

    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Brands', 'url': reverse('providers:vendor_brand_list')},
        {'title': f'Delete {brand.name}', 'url': None}
    ]

    if request.method == 'POST':
        vendor_brand.delete()

        # Check if any other vendor still uses this brand
        if not VendorBrand.objects.filter(brand=brand).exists():
            brand.delete()

        messages.success(request, 'Brand deleted successfully.')
        return redirect('providers:vendor_brand_list')

    return render(request, 'providers/vendor_brand_confirm_delete.html', {
        'brand': vendor_brand,
        'breadcrumbs': breadcrumbs
    })

# ----------------------------
# CATEGORY VIEWS
# ----------------------------
@vendor_required
def vendor_category_list(request):
    vendor = get_vendor(request.user)
    categories = VendorCategory.objects.filter(vendor=vendor)
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Categories', 'url': None}
    ]
    return render(request, 'providers/vendor_category_list.html', {'categories': categories, 'breadcrumbs': breadcrumbs})

@vendor_required
def vendor_category_create(request):
    vendor = get_vendor(request.user)
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Categories', 'url': reverse('providers:vendor_category_list')},
        {'title': 'Add Category', 'url': None}
    ]
    if request.method == 'POST':
        form = VendorCategoryForm(request.POST, vendor=vendor)
        if form.is_valid():
            form.save(vendor=vendor)
            messages.success(request, 'Category created successfully.')
            return redirect('providers:vendor_category_list')
    else:
        form = VendorCategoryForm(vendor=vendor)
    return render(request, 'providers/vendor_category_form.html', {'form': form, 'breadcrumbs': breadcrumbs})

@vendor_required
def vendor_category_update(request, pk):
    vendor = get_vendor(request.user)
    vendor_category = get_object_or_404(VendorCategory, pk=pk, vendor=vendor)
    category = vendor_category.category 
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Categories', 'url': reverse('providers:vendor_category_list')},
        {'title': f'Edit {category.name}', 'url': None}
    ]
    if request.method == 'POST':
        form = VendorCategoryForm(request.POST, instance=category, vendor=vendor)
        if form.is_valid():
            form.save(vendor=vendor)
            messages.success(request, 'Category updated successfully.')
            return redirect('providers:vendor_category_list')
    else:
        form = VendorCategoryForm(instance=category, vendor=vendor)
    return render(request, 'providers/vendor_category_form.html', {'form': form, 'breadcrumbs': breadcrumbs})

@vendor_required
def vendor_category_delete(request, pk):
    vendor = get_vendor(request.user)
    vendor_category = get_object_or_404(VendorCategory, pk=pk, vendor=vendor)
    category = vendor_category.category

    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Categories', 'url': reverse('providers:vendor_category_list')},
        {'title': f'Delete {category.name}', 'url': None}
    ]

    if request.method == 'POST':
        vendor_category.delete()

        # Delete the global Category only if no other vendor is using it
        if not VendorCategory.objects.filter(category=category).exists():
            category.delete()

        messages.success(request, 'Category deleted successfully.')
        return redirect('providers:vendor_category_list')

    return render(request, 'providers/vendor_category_confirm_delete.html', {
        'category': vendor_category,
        'breadcrumbs': breadcrumbs
    })

# ----------------------------
# PRODUCT VIEWS
# ----------------------------
@vendor_required
def vendor_product_list(request):
    vendor = get_vendor(request.user)
    vendor_products = VendorProduct.objects.filter(vendor=vendor).select_related('product')
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Products', 'url': None}
    ]
    context = {
            'vendor_products': vendor_products,
            'breadcrumbs': breadcrumbs
        }
    return render(request, 'providers/vendor_product_list.html', context)

@vendor_required
def vendor_product_create(request):
    vendor = get_vendor(request.user)
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Products', 'url': reverse('providers:vendor_product_list')},
        {'title': 'Add Product', 'url': None}
    ]
    if request.method == 'POST':
        form = VendorProductForm(request.POST, request.FILES, vendor=vendor)
        if form.is_valid():
            product = form.save(vendor=vendor)
            messages.success(request, 'Product created successfully.')
            return redirect('providers:vendor_variation_create', product_pk=product.id)


    else:
        form = VendorProductForm(vendor=vendor)
    context = {
        'form': form,
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'providers/vendor_product_form.html', context)

@vendor_required
def vendor_product_update(request, pk):
    vendor = get_vendor(request.user)
    vendor_product = get_object_or_404(VendorProduct, pk=pk, vendor=vendor)
    product = vendor_product.product

    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Products', 'url': reverse('providers:vendor_product_list')},
        {'title': f'Edit {product.name}', 'url': None}
    ]

    if request.method == 'POST':
        form = VendorProductForm(request.POST, request.FILES, instance=product, vendor=vendor)
        if form.is_valid():
            form.save(vendor=vendor)
            messages.success(request, 'Product updated successfully.')
            return redirect('providers:vendor_product_list')
    else:
        form = VendorProductForm(instance=product, vendor=vendor)

    return render(request, 'providers/vendor_product_form.html', {
        'form': form,
        'product': product,
        'breadcrumbs': breadcrumbs
    })

@vendor_required
def vendor_product_delete(request, pk):
    vendor = get_vendor(request.user)
    vendor_product = get_object_or_404(VendorProduct, pk=pk, vendor=vendor)
    product = vendor_product.product

    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Products', 'url': reverse('providers:vendor_product_list')},
        {'title': f'Delete {product.name}', 'url': None}
    ]

    if request.method == 'POST':
        vendor_product.delete()  # remove vendor link

        # Optional: delete the product only if no other vendors are linked to it
        if not VendorProduct.objects.filter(product=product).exists():
            product.delete()

        messages.success(request, 'Product deleted successfully.')
        return redirect('providers:vendor_product_list')

    return render(request, 'providers/vendor_product_confirm_delete.html', {
        'product': vendor_product,
        'breadcrumbs': breadcrumbs
    })

# ----------------------------
# VARIATION VIEWS
# ----------------------------
@vendor_required
def vendor_variation_list(request, product_pk):
    vendor = get_vendor(request.user)
    product = get_object_or_404(Product, id=product_pk)
    
    # Check if this product belongs to the vendor
    if not VendorProduct.objects.filter(vendor=vendor, product=product).exists():
        messages.error(request, "You don't have permission to view this product's variations.")
        return redirect('providers:vendor_product_list')
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Products', 'url': reverse('providers:vendor_product_list')},
        {'title': product.name, 'url': None},
        {'title': 'Variations', 'url': None}
    ]
    variations = product.variations.all()
    context = {
        'product': product,
        'variations': variations,
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'providers/vendor_variation_list.html', context)

@vendor_required
def vendor_variation_create(request, product_pk):
    vendor = get_vendor(request.user)
    product = get_object_or_404(Product, id=product_pk)

    if not VendorProduct.objects.filter(vendor=vendor, product=product).exists():
        messages.error(request, "You don't have permission to modify this product.")
        return redirect('providers:vendor_product_list')
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Products', 'url': reverse('providers:vendor_product_list')},
        {'title': product.name, 'url': reverse('providers:vendor_variation_list', kwargs={'product_pk': product_pk})},
        {'title': 'Add Variation', 'url': None}
    ]
    if request.method == 'POST':
        form = ProductVariationForm(request.POST, request.FILES, product=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Variation added successfully.')
            return redirect('providers:vendor_variation_list', product_pk=product_pk)
    else:
        form = ProductVariationForm(product=product)

    variations = product.variations.all()
    context = {
        'form': form,
        'product': product,
        'variations': variations,
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'providers/vendor_variation_form.html', context)

@vendor_required
def vendor_variation_update(request,product_pk, pk):
    variation = get_object_or_404(ProductVariation, pk=pk)
    vendor = get_vendor(request.user)
    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Products', 'url': reverse('providers:vendor_product_list')},
        {'title': variation.product.name, 'url': reverse('providers:vendor_variation_list', kwargs={'product_pk': variation.product.id})},
        {'title': f'Edit Variation', 'url': None}
    ]
    if not VendorProduct.objects.filter(vendor=vendor, product=variation.product).exists():
        messages.error(request, "You don't have permission to edit this variation.")
        return redirect('providers:vendor_variation_list')

    if request.method == 'POST':
        form = ProductVariationForm(request.POST, request.FILES, instance=variation, product=variation.product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Variation updated successfully.')
            return redirect('providers:vendor_variation_list')
    else:
        form = ProductVariationForm(instance=variation, product=variation.product)

    return render(request, 'providers/vendor_variation_form.html', {
        'form': form,
        'product': variation.product,
        'variation': variation,
        'breadcrumbs': breadcrumbs
    })

@vendor_required
def vendor_variation_delete(request, product_pk, pk):
    variation = get_object_or_404(ProductVariation, pk=pk)
    vendor = get_vendor(request.user)

    breadcrumbs = [
        {'title': 'Dashboard', 'url': reverse('providers:vendor_dashboard')},
        {'title': 'Products', 'url': reverse('providers:vendor_product_list')},
        {'title': variation.product.name, 'url': reverse('providers:vendor_variation_list', kwargs={'product_pk': variation.product.id})},
        {'title': 'Delete Variation', 'url': None}
    ]

    if not VendorProduct.objects.filter(vendor=vendor, product=variation.product).exists():
        messages.error(request, "You don't have permission to delete this variation.")
        return redirect('providers:vendor_variation_list', product_pk=product_pk)

    if request.method == 'POST':
        variation.delete()
        messages.success(request, 'Variation deleted successfully.')
        return redirect('providers:vendor_variation_list', product_pk=product_pk)

    return render(request, 'providers/vendor_variation_confirm_delete.html', {
        'variation': variation,
        'product': variation.product,
        'breadcrumbs': breadcrumbs
    })

# ----------------------------
# STATIC PAGES
# ----------------------------
def about(request):
    return render(request, 'tags/about.html')

def contact(request):
    return render(request, 'tags/contact.html')

def terms(request):
    return render(request, 'tags/terms.html')
