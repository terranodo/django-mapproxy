from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from .models import Tileset

class TilesetAdmin(GuardedModelAdmin):
    readonly_fields = ('size', 'layer_uuid',)
    list_display = ('name', 'layer_name', 'server_url', 'created_by', 'created_at')
    search_fields = ['name']

admin.site.register(Tileset, TilesetAdmin)
