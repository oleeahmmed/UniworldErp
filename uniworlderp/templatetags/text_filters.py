from django import template

register = template.Library()


@register.filter
def clean_address(value):
    """Strips stray backslash-escapes (e.g. "1109\\, A\\B" -> "1109, A/B")
    left over in some addresses from data import, without touching the
    stored value."""
    if not value:
        return value
    return value.replace('\\', '')
