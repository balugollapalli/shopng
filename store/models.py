from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Count, F, FloatField, ExpressionWrapper, Avg, Q


class Brand(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='brand_logos/', blank=True, null=True)
    founded_year = models.IntegerField(null=True, blank=True)
    website = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Brands'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:brand_detail', kwargs={'slug': self.slug})

    def get_product_count(self):
        return self.products.count()

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)  # Allow blank
    description = models.TextField(blank=True)
    brands = models.ManyToManyField('Brand', related_name='categories', blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:product_list_by_category', args=[self.slug])

    def get_product_count(self):
        return self.products.count()


class ProductQuerySet(models.QuerySet):  
    def available(self):
        return self.filter(available=True, stock__gt=0)

    def discounted(self):
        return self.filter(discount_percentage__gt=0)

    def search(self, query):
        return self.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__name__icontains=query) |
            Q(category__name__icontains=query)  
        )


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def available(self):
        return self.get_queryset().available()

    def discounted(self):
        return self.get_queryset().discounted()

    def search(self, query):
        return self.get_queryset().search(query)


class Product(models.Model):
    brand = models.ForeignKey('Brand', related_name='products', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    description = models.TextField(blank=True) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)   
    discount_percentage = models.IntegerField(default=0)
    stock = models.PositiveIntegerField()
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    objects = ProductManager()
    class Meta:
        ordering = ('-created',)
        indexes = [models.Index(fields=['id', 'slug']),models.Index(fields=['name', 'slug']),]
    
    def save(self, *args, **kwargs):
        if self.price is not None and self.discount_percentage and not self.original_price:
            self.original_price = self.price / (1 - (Decimal(self.discount_percentage) / 100))
        elif self.original_price and self.price:
            if self.original_price > self.price:
                self.discount_percentage = int(
                    ((self.original_price - self.price) / self.original_price) * 100
                )
            else:
                self.discount_percentage = 0
        elif self.original_price and self.discount_percentage and not self.price:
            discount_amount = (self.original_price * Decimal(self.discount_percentage)) / Decimal(100)
            self.price = self.original_price - discount_amount
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)
        
    def generate_unique_slug(self):
        base_slug = slugify(self.name)
        unique_slug = base_slug
        counter = 1
        while Product.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        return unique_slug
    
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])
    
    def get_reviews(self):
        return self.reviews.all().order_by('-created_at')
    
    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    def total_reviews(self):
        return self.reviews.count()
    def rating_distribution(self):
        total_reviews = self.total_reviews()
        distribution = {
            1: {'count': 0, 'percentage': 0},
            2: {'count': 0, 'percentage': 0},
            3: {'count': 0, 'percentage': 0},
            4: {'count': 0, 'percentage': 0},
            5: {'count': 0, 'percentage': 0}
        }
        rating_counts = self.reviews.values('rating').annotate(count=Count('rating'))
        for item in rating_counts:
            rating = item['rating']
            count = item['count']
            distribution[rating]['count'] = count
            distribution[rating]['percentage'] = (count / total_reviews * 100) if total_reviews > 0 else 0
        return distribution
    
    def is_in_stock(self):
        return self.stock > 0 
    
    def get_discounted_price(self):
        return self.price if self.discount_percentage == 0 else self.original_price
        
    def related_products(self, limit=4):
        return Product.objects.filter(
            Q(category=self.category) | Q(brand=self.brand),
            available=True  
        ).exclude(id=self.id).order_by('?')[:limit] 
         


class ProductVariation(models.Model):  
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations')
    name = models.CharField(max_length=50)  
    value = models.CharField(max_length=50)  
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='variation_images/', null=True, blank=True) 
    

    class Meta:
        unique_together = ('product', 'name', 'value')

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey('Product',  on_delete=models.CASCADE, related_name='wishlist_items')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username}'s wishlist - {self.product.name}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=200, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ('-created',)
    
    def __str__(self):
        return f'Order {self.id}'
    
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    variation = models.ForeignKey(ProductVariation, on_delete=models.SET_NULL, null=True, blank=True)
    variation_name = models.CharField(max_length=100, blank=True, null=True)
    variation_value = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return str(self.id)
    
    def get_cost(self):
        return self.price * self.quantity

class UserAddress(models.Model):
    ADDRESS_TYPES = (('home', 'Home'),('work', 'Work'),('other', 'Other'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')  
    name = models.CharField(max_length=100)  
    street_address = models.CharField(max_length=255)
    apartment_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='home')
    is_default = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'User Addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.address_type} Address"

    def save(self, *args, **kwargs):
        if self.is_default:
            UserAddress.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'order')
        indexes = [
            models.Index(fields=['product', 'created_at']),
        ]