from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib.auth.decorators import login_required

from .models import Tileset
import time
import json


class IndexView(generic.ListView):
    template_name = 'djmp/index.html'

    def get_queryset(self):
        return Tileset.objects.all()


class DetailView(generic.DetailView):
    model = Tileset
    template_name = 'djmp/tileset_detail.html'


@login_required
def seed(request, pk):
    tileset = get_object_or_404(Tileset, pk=pk)
    return HttpResponse(json.dumps(tileset.seed()))