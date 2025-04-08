from django import forms
from django.contrib.auth.models import User
from store.models import *
from .models import *
import itertools
from django.utils.text import slugify


class VendorLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class VendorUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    shop_name = forms.CharField(label='Shop Name', max_length=255)

    class Meta:
        model = VendorUser
        fields = ['email', 'full_name']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class VendorBrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'description', 'logo', 'founded_year', 'website']

    def save(self, vendor, commit=True):
        brand = super().save(commit)
        VendorBrand.objects.get_or_create(vendor=vendor, brand=brand)
        return brand

class VendorCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'brands']

    def __init__(self, *args, **kwargs):
        vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)
        if vendor:
            # Limit brand selection to brands owned by this vendor
            self.fields['brands'].queryset = Brand.objects.filter(
                id__in=VendorBrand.objects.filter(vendor=vendor).values_list('brand_id', flat=True)
            )

    def save(self, vendor, commit=True):
        category = super().save(commit)
        VendorCategory.objects.get_or_create(vendor=vendor, category=category)
        return category

class VendorProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['brand', 'category', 'name', 'image', 'description', 'price',
                  'original_price', 'discount_percentage', 'stock', 'available']

    def __init__(self, *args, **kwargs):
        vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)
        if vendor:
            self.fields['brand'].queryset = Brand.objects.filter(
                id__in=VendorBrand.objects.filter(vendor=vendor).values_list('brand_id', flat=True)
            )
            self.fields['category'].queryset = Category.objects.filter(
                id__in=VendorCategory.objects.filter(vendor=vendor).values_list('category_id', flat=True)
            )

    def save(self, vendor, commit=True):
        product = super().save(commit=False)
        base_slug = slugify(product.name)
        slug = base_slug
        for i in itertools.count(1):
            if not Product.objects.filter(slug=slug).exists():
                break
            slug = f"{base_slug}-{i}"
        product.slug = slug

        if commit:
            product.save()
        VendorProduct.objects.get_or_create(vendor=vendor, product=product)
        return product

class ProductVariationForm(forms.ModelForm):
    class Meta:
        model = ProductVariation
        fields = ['name', 'value', 'price', 'stock', 'image']

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        variation = super().save(commit=False)
        if self.product:
            variation.product = self.product
        if commit:
            variation.save()
        return variation
