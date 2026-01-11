from django import template

register = template.Library()

@register.filter
def zip_lists(list1, list2):
    """Zip two lists together for iteration"""
    return zip(list1, list2)

@register.filter
def get_item(lst, index):
    """Get item from list by index"""
    try:
        return lst[index]
    except (IndexError, TypeError):
        return ''
