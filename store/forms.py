from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *  
from django.core.validators import RegexValidator

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'description', 'logo', 'founded_year', 'website']
        widgets = {  
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'founded_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'brands']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'brands': forms.CheckboxSelectMultiple
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'brand', 'category', 'image','description', 'price', 'original_price','stock', 'available']
        widgets = {  
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'original_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductVariationForm(forms.ModelForm): 
    class Meta:
        model = ProductVariation
        fields = ['name', 'value', 'price', 'stock']
        widgets = {
            'name': forms.Select(attrs={'class': 'form-control'}),  
            'value': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class WishlistForm(forms.ModelForm):
    class Meta:
        model = Wishlist
        fields = ['user', 'product'] 

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'city', 'state', 'postal_code', 'country', 'phone']

class ProductSearchForm(forms.Form):
    query = forms.CharField(required=False, label='Search', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search products'}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False,empty_label="All Categories",widget=forms.Select(attrs={'class': 'form-select'}))
    brand = forms.ModelChoiceField(queryset=Brand.objects.all(), required=False,empty_label="All Brands",widget=forms.Select(attrs={'class': 'form-select'}))
    min_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Price'}))
    max_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Price'}))
    sort_by = forms.ChoiceField(required=False,
        choices=[('name', 'Name'),('price_asc', 'Price: Low to High'),('price_desc', 'Price: High to Low'),('newest', 'Newest First'),],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class UserAddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = ['name', 'street_address', 'apartment_address', 'city', 'state', 'postal_code', 'country', 'address_type', 'phone_number', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control'}),
            'apartment_address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
