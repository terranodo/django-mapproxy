from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views import generic
from .models import Tileset
import time


class IndexView(generic.ListView):
    template_name = 'djmp/index.html'

    def get_queryset(self):
        return Tileset.objects.all()


class DetailView(generic.DetailView):
    model = Tileset
    template_name = 'djmp/tileset_detail.html'
