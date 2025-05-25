from django import template

register = template.Library()

@register.filter
def to(value):
    """Returns a list from 1 to value inclusive."""
    try:
        return range(1, int(value) + 1)
    except Exception:
        return []

@register.filter
def rangefilter(value):
    """Returns range from 0 to value exclusive."""
    try:
        return range(int(value))
    except Exception:
        return []
