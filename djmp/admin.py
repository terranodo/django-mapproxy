from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from .models import Tileset


def seed_action(modeladmin, request, queryset):
    for tileset in queryset:
        tileset.seed()

seed_action.short_description = "Seed selected Tilesets"


class TilesetAdmin(GuardedModelAdmin):
    readonly_fields = ('size', 'layer_uuid',)
    list_display = ('id', 'name', 'layer_name', 'server_url', 'created_by', 'created_at')
    search_fields = ['name']
    actions = [seed_action]

admin.site.register(Tileset, TilesetAdmin)
