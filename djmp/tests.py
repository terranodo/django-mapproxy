from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from .views import tileset_status, seed
from .models import Tileset


class DjmpTest(TestCase):

    fixtures = ['test_data.json']

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        self.client = Client()

    def test_seeding(self):
        """ test seeding"""
        self.client.login(username='admin', password='admin')
        resp = self.client.get(reverse('tileset_seed', args=(1,)))
        self.assertEqual('{"status": "started"}', resp.content)