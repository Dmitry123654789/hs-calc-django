from django import template

register = template.Library()


@register.filter(name="get_or_self")
def get_or_self(key, mapping):
    if isinstance(mapping, dict) and key in mapping:
        return mapping[key]

    return key
