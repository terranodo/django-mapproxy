from django.conf import settings

FILE_CACHE_DIRECTORY = getattr('settings', 'FILE_CACHE_DIRECTORY', 'cache/layers')
