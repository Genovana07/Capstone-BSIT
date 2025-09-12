from django import template
import math

register = template.Library()

@register.filter
def star_counts(value):
    """Return a dict with full, half, and empty stars."""
    try:
        rating = float(value)
    except (TypeError, ValueError):
        rating = 0

    full = int(math.floor(rating))
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half

    return {"full": range(full), "half": range(half), "empty": range(empty)}
