from django.contrib.auth.backends import BaseBackend
from providers.models import VendorUser

class EmailBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = VendorUser.objects.get(email=email)
            if user.check_password(password):
                return user
        except VendorUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return VendorUser.objects.get(pk=user_id)
        except VendorUser.DoesNotExist:
            return None
