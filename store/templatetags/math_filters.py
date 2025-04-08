from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        return value

@register.filter(name='subtract')
def subtract(value, arg):
    try:  
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return ''  