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
import re, datetime, time
from pprint import pprint

import flask
from flask import json, g

from cloudapp.api import Envelope
from cloudapp.permissions import valid_user
from cloudapp.authentication.endpoints import api as AuthAPI

from framework import TestingFramework, json_content_header, basic_auth_header

@AuthAPI.route('/notsosecret')
def not_so_secret():
    envelope = Envelope()
    return envelope.send()

@AuthAPI.route('/supersecret')
@valid_user.require(http_exception=403)
def super_secret():
    envelope = Envelope()
    envelope.add_meta('secret','shhhhh')
    return envelope.send()

class AuthenticationTests(TestingFramework):
   
    def setupUserAccounts(self):
        with self.app.test_request_context('/'):
             self.app.preprocess_request()
             g.User(email="thesis@finish.it", password="never",email_verified=True).store()
             g.User(email="the.dude@gmail.com",password="rug",email_verified=True).store()

    def testUserAccountsUsingGmailAndGlobalCouchContext(self):
        with self.app.test_request_context('/'):
             self.app.preprocess_request()
             self.setupUserAccounts()
             user = g.User.load("the.dude@gmail.com")
             self.assertEqual(user.email, "the.dude@gmail.com")
             self.assertEqual(user.id, "thedude@gmail.com")

    def testOtherUserAccountsAndGlobalCouchContext(self):
        with self.app.test_request_context('/'):
             self.app.preprocess_request()
             self.setupUserAccounts()
             user = g.User.load("thesis@finish.it")
             self.assertEqual(user.id, "thesis@finish.it")
             self.assertEqual(user.email, "thesis@finish.it")

    def testCreateAccountWithValidData(self):
        user=dict(first_name="Matt", last_name="Coyle", email="thesis@finish.it", password="never")
        data=dict(user=user, device_info=self.device_info)
        rv = self.testclient.post('/api/v1/auth/signup', content_type='application/json', data=json.dumps(data))
        assert '201' in rv.data

    def testCreateAccountWithInvalidFieldValues(self):
        user=dict(first_name="Matt", last_name="Coyle", email="thesis@finishit", password="never")
        data=dict(user=user, device_info=self.device_info)
        rv = self.testclient.post('/api/v1/auth/signup', content_type='application/json', data=json.dumps(data))
        assert '400' in rv.data

    def testCreateAccountWithRequiredFieldsMissing(self):
        user=dict(first_name="Matt", last_name="Coyle", password="never")
        data=dict(user=user, device_info=self.device_info)
        rv = self.testclient.post('/api/v1/auth/signup', content_type='application/json', data=json.dumps(data))
        assert '400' in rv.data

    def testValidLoginAndPermanentSession(self):
        self.setupUserAccounts()
        data = self.device_info
        rv = self.testclient.post('/api/v1/auth/login', content_type='application/json', 
                  data=json.dumps(data), headers=[basic_auth_header("thesis@finish.it", "never")])
        assert 'token' in rv.data
        assert '201' in rv.data
        assert 'set-cookie' in rv.headers
        match = re.search(r'\bexpires=([^;]+)', rv.headers['set-cookie'])
        assert match is not None
        rv = self.testclient.get('/api/v1/auth/supersecret')
        self.assertIn('secret', rv.data)

    def testValidLoginWithoutDeviceInfo(self):
        self.setupUserAccounts()
        data = None
        rv = self.testclient.post('/api/v1/auth/login', content_type='application/json', 
                  data=json.dumps(data), headers=[basic_auth_header("thesis@finish.it", "never")])
        assert '400' in rv.data

    def testInvalidLoginWithIncorrectPassword(self):
        self.setupUserAccounts()
        rv = self.testclient.post('/api/v1/auth/login', content_type='application/json',
                  data=dict(device_info="flask.test_client"),
                  headers=[json_content_header, basic_auth_header("thesis@finish.it", "done")])
        assert '401' in rv.data

    def testInvalidLoginWithInvalidUsername(self):
        self.setupUserAccounts()
        rv = self.testclient.post('/api/v1/auth/login', 
                  data=dict(device_info="flask.test_client"), content_type='application/json',
                  headers=[json_content_header, basic_auth_header("thesis.coyle@finish.it", "done")])
        assert '401' in rv.data

    def testRepeatedUnsuccessfulLogins(self):
        pass

    def testValidTokenAuthentication(self):
        with self.app.test_request_context('/'):
             self.app.preprocess_request()
             self.setupUserAccounts()
             user = g.User.load("thesis@finish.it")
             assert user is not None
             token = user.create_session(device_info=dict(client='flask.test_client'))
             assert token is not None
        with self.app.test_client() as c:
             try:
                 assert 'identity.id' not in flask.session
                 self.fail('identity.id should not be found in the session')
             except RuntimeError:
                 pass 
             rv = c.get('/api/v1/auth/supersecret', headers=[('X-Auth-Token',token)])
             assert 'identity.id' in flask.session
             #assert flask.session['loaded_from'] == 'couchdb'
             rv = c.get('/api/v1/auth/supersecret', headers=[('X-Auth-Token',token)])
             self.assertIn('secret', rv.data)
             #assert flask.session['loaded_from'] == 'memcached'
             rv = c.get('/api/v1/auth/logout', headers=[('X-Auth-Token',token)])
             assert '200' in rv.data
             assert flask.session['identity.id'] == 'anon'
             rv = c.get('/api/v1/auth/supersecret', headers=[('X-Auth-Token',token)])
             assert '403' in rv.data

    def testInvalidTokenAuthentication(self):
        token = 'invalid-token'
        rv = self.testclient.get('/api/v1/auth/supersecret', base_url=self.base_url, headers=[('X-Auth-Token',token)])
        self.assertNotIn('secret', rv.data)
        self.assertIn('403', rv.data)
        assert 'set-cookie' not in rv.headers

    def testNonProtectedEndPoint(self):
        rv = self.testclient.get('/api/v1/auth/notsosecret', base_url=self.base_url)
        assert 'set-cookie' not in rv.headers
        
