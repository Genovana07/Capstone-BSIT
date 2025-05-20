# custom_filters.py
from django import template

register = template.Library()

@register.filter
def to(value):
    """Returns a list of numbers from 1 to value (inclusive)."""
    return range(1, value + 1)

@register.filter
def rangefilter(value):
    """Create a range from 0 to value."""
    return range(value)