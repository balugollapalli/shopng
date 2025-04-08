from django.db import models
from django.conf import settings
from store.models import Brand, Category, Product
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import Group, Permission

class VendorUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Vendors must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class VendorUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        related_name='vendoruser_set',
        blank=True,
        help_text='The groups this vendor belongs to.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='vendoruser_set',
        blank=True,
        help_text='Specific permissions for this vendor.',
        verbose_name='user permissions'
    )

    objects = VendorUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.full_name
    
    @property
    def username(self):
        return self.email

class Vendor(models.Model):
    user = models.OneToOneField('VendorUser', on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=255)
    # Additional fields like logo, address, etc.

    def __str__(self):
        return self.shop_name


# Optional: Proxy models or vendor-specific models (not stored in DB separately)

class VendorBrand(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='brands')
    brand = models.OneToOneField(Brand, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.brand.name} (by {self.vendor.name})"


class VendorCategory(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='categories')
    category = models.OneToOneField(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.category.name} (by {self.vendor.name})"


class VendorProduct(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    product = models.OneToOneField(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.name} (by {self.vendor.name})"
