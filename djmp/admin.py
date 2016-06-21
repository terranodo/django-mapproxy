from django.contrib import admin

from .models import Tileset

class TilesetAdmin(admin.ModelAdmin):
    readonly_fields=('size',)
    list_display = ('name', 'layer_name', 'server_url', 'created_by', 'created_at')
    search_fields = ['name']

admin.site.register(Tileset, TilesetAdmin)
