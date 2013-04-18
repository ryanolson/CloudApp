# -*- coding: utf-8 -*-
"""
Copyright 2013 Ryan Olson

This file is part of CloudApp.

CloudApp is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CloudApp is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CloudApp.  If not, see <http://www.gnu.org/licenses/>.
"""
import unittest
from cloudapp import Application, BaseUser
from cloudapp.config import TestingConfig

json_content_header = ('Content-Type', 'application/json')

def basic_auth_header(username, password):
    import base64
    return ('Authorization', 'Basic ' + base64.b64encode(username + ":" + password))


class TestingFramework(unittest.TestCase):

    class User(BaseUser):
        pass

    class MyTestingConfig(TestingConfig):
        SERVER_NAME = 'osila.dev:8080'
        SECRET_KEY  = 'hi'

    @property
    def db(self):
        with self.app.app_context():
             return self.webapp.couch.db

    def setUp(self):
        self.app = Application.flask("OsilaTests", self.MyTestingConfig)
        self.webapp = Application(self.User, self.app)
        self.testclient = self.app.test_client()
        self.base_url = "http://api.{}".format(self.app.config['SERVER_NAME'])
        self.device_info = dict(device_info=dict(name='flask.test_client'))

    def tearDown(self):
        try:
            server = self.webapp.couch.server
            server.delete(self.webapp.couch.db_name)
        except:
            pass

    def testURL(self):
        assert self.base_url == "http://api.osila.dev:8080"
