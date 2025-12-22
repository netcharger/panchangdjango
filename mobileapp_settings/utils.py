"""
Utility functions for accessing site settings easily.
"""
from .models import SiteSetting


def get_setting(key, default=None):
    """
    Get a site setting value by key.
    
    Args:
        key (str): The setting key to retrieve
        default: Default value to return if setting not found or inactive
    
    Returns:
        The setting value (type depends on value_type) or default
    
    Example:
        >>> site_title = get_setting('site_title', 'Default Title')
        >>> hero_image = get_setting('hero_image')
    """
    try:
        setting = SiteSetting.objects.get(key=key, is_active=True)
        return setting.get_value()
    except SiteSetting.DoesNotExist:
        return default


def get_all_settings():
    """
    Get all active site settings as a dictionary.
    
    Returns:
        dict: Dictionary with keys as setting keys and values as dictionaries
              containing 'value', 'value_type', and 'description'
    
    Example:
        >>> settings = get_all_settings()
        >>> print(settings['site_title']['value'])
        'My Panchang App'
    """
    settings_dict = {}
    for setting in SiteSetting.objects.filter(is_active=True):
        settings_dict[setting.key] = {
            'value': setting.get_value(),
            'value_type': setting.value_type,
            'description': setting.description
        }
    return settings_dict


def get_settings_dict():
    """
    Get all active site settings as a simple key-value dictionary.
    Only returns the values, not metadata.
    
    Returns:
        dict: Simple dictionary mapping setting keys to their values
    
    Example:
        >>> settings = get_settings_dict()
        >>> print(settings['site_title'])
        'My Panchang App'
    """
    settings_dict = {}
    for setting in SiteSetting.objects.filter(is_active=True):
        settings_dict[setting.key] = setting.get_value()
    return settings_dict
























