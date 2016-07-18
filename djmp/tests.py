from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from guardian.management import create_anonymous_user
from guardian.shortcuts import remove_perm

from .views import tileset_status, seed
from .models import Tileset


class DjmpTestBase(TestCase):

    fixtures = ['test_data.json']

    def setUp(self):
        super(DjmpTestBase, self).setUp()
        create_anonymous_user(None)

        self.user = 'admin'
        self.passwd = 'admin'
        self.client = Client()


class DjmpTest(DjmpTestBase):
    def test_seeding(self):
        """ test seeding"""
        self.client.login(username='admin', password='admin')
        resp = self.client.get(reverse('tileset_seed', args=(1,)))
        self.assertEqual('{"status": "started"}', resp.content)


class TilesetTestBase(DjmpTestBase):
    def setUp(self):
        super(TilesetTestBase, self).setUp()
        self.headers = {
            # TODO(mvv): these headers are specific to mvv's local env, that 
            #            may be bad long term
            'X-Script-Name': '/1/map/tms/1.0.0/test/EPSG3857/1/0/0.png',
            'HTTP_HOST': 'localhost:8000',
            'SERVER_NAME': 'michaels-macbook-pro-2.local',
            'X-Forwarded-Host': 'localhost:8000'
        }
        # seed tile
        resp = self.client.get(reverse('tileset_seed', args=(1,)))


class TilesetAuthTest(TilesetTestBase):
    def setUp(self):
        super(TilesetAuthTest, self).setUp()
        self.testuser = User.objects.create_user(
            'testuser',
            'testuser@mvavnveen.net',
            'testuser'
        )
        self.testuser.save()

        self.uri = reverse(
            'tileset_mapproxy',
            args=(1, u'/tms/1.0.0/streams/EPSG3857/1/0/0.png')
        )

    def test_not_authorized_anonymous(self):
        res = self.client.get(self.uri, **self.headers)
        self.assertEqual(res.status_code, 403)

    def test_authorized_admin(self):
        self.client.login(username='admin', password='admin')
        res = self.client.get(self.uri, **self.headers)
        self.assertEqual(res.status_code, 200)

    def test_not_authorized_remove_perm(self):
        self.client.login(username='testuser', password='testuser')
        res = self.client.get(self.uri, **self.headers)
        self.assertEqual(res.status_code, 403)

    def test_authorized_test_user_make_perm(self):
        self.client.login(username='testuser', password='testuser')
        res = self.client.get(self.uri, **self.headers)
        self.assertEqual(res.status_code, 403)

        tileset = Tileset.objects.get(pk=1)
        tileset.add_read_perm(self.testuser)

        self.client.login(username='testuser', password='testuser')
        res = self.client.get(self.uri, **self.headers)
        self.assertEqual(res.status_code, 200)

        remove_perm('view_tileset', self.testuser, tileset)
        self.client.login(username='testuser', password='testuser')
        res = self.client.get(self.uri, **self.headers)
        self.assertEqual(res.status_code, 403)
