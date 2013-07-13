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
from couchdb.tests import testutil
from cloudapp import CloudApp, BaseUser
from cloudapp.config import TestingConfig

json_content_header = ('Content-Type', 'application/json')

def basic_auth_header(username, password):
    import base64
    return ('Authorization', 'Basic ' + base64.b64encode(username + ":" + password))


class TestingFramework(testutil.TempDatabaseMixin, unittest.TestCase):

    class User(BaseUser):
        pass

    class MyTestingConfig(TestingConfig):
        SECRET_KEY  = 'hi'

    def setUp(self):
        super(TestingFramework,self).setUp()
        self.app = CloudApp.flask("OsilaTests", self.MyTestingConfig)
        self.webapp = CloudApp(self.User, app=self.app, server=self.server, db=self.db)
        self.testclient = self.app.test_client()
        self.base_url = "http://localhost"
        self.device_info = dict(device_info=dict(name='flask.test_client'))

    def testURL(self):
        assert self.base_url == "http://localhost"
