from django import template
from store.models import *

register = template.Library()

@register.simple_tag(takes_context=True)  
def get_wishlist_count(context):
    request = context['request']
    if request.user.is_authenticated:
        return Wishlist.objects.filter(user=request.user).count()
    return 0
