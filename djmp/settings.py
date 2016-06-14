from django.conf import settings

CACHE_CONFIG = getattr('settings', 'CACHE_CONFIG', {
    'type': 'file',
    'directory': 'cache',
    'directory_layout': 'tms'
})