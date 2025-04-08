from django.contrib import admin
from .models import Brand, Category, Product, ProductVariation

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'founded_year', 'website', 'get_product_count',)
    prepopulated_fields = {'slug': ('name',)}
    
    def get_product_count(self, obj):
        return obj.get_product_count()
    get_product_count.short_description = 'Product Count'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'get_product_count',)
    prepopulated_fields = {'slug': ('name',)}
    
    def get_product_count(self, obj):
        return obj.get_product_count()
    get_product_count.short_description = 'Product Count'
    
class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'price', 'available', 'stock', 'created', 'updated', 'discount_percentage',)
    list_filter = ('available', 'brand', 'category', 'created', 'updated')
    list_editable = ('price', 'available', 'stock')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariationInline]
