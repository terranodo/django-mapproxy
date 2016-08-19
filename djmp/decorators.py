from functools import wraps

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .models import Tileset
from .settings import ENABLE_GUARDIAN_PERMISSIONS

def view_tileset_permissions(view_func):
    def _wrapped_view(request, *args, **kwargs):
        tileset_pk = kwargs.get('pk')

        # if permissions aren't enabled just pass through
        if ENABLE_GUARDIAN_PERMISSIONS == False:
            return view_func(request, *args, **kwargs)

        if tileset_pk is None:
            raise ValueError('no tileset pk provided')

        tileset = get_object_or_404(Tileset, pk=tileset_pk)
        allowed = request.user.has_perm('view_tileset', tileset)

        if not allowed:
            response = HttpResponse("forbidden", status=403)
            return response

        return view_func(request, *args, **kwargs)

    return wraps(view_func)(_wrapped_view)
