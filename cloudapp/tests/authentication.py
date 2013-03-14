# -*- coding: utf-8 -*-
import unittest
import re, datetime, time
from pprint import pprint

import flask
from flask import json, g

from cloudapp.api import Envelope
from cloudapp.tests.framework import TestingFramework, json_content_header, basic_auth_header
from cloudapp.permissions import valid_user
from cloudapp.authentication.endpoints import api as AuthAPI

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
        rv = self.testclient.post('/auth/signup', base_url=self.base_url, content_type='application/json', data=json.dumps(data))
        assert '201' in rv.data

    def testCreateAccountWithInvalidFieldValues(self):
        user=dict(first_name="Matt", last_name="Coyle", email="thesis@finishit", password="never")
        data=dict(user=user, device_info=self.device_info)
        rv = self.testclient.post('/auth/signup', base_url=self.base_url, content_type='application/json', data=json.dumps(data))
        assert '400' in rv.data

    def testCreateAccountWithRequiredFieldsMissing(self):
        user=dict(first_name="Matt", last_name="Coyle", password="never")
        data=dict(user=user, device_info=self.device_info)
        rv = self.testclient.post('/auth/signup', base_url=self.base_url, content_type='application/json', data=json.dumps(data))
        assert '400' in rv.data

    def testValidLoginAndPermanentSession(self):
        self.setupUserAccounts()
        data = self.device_info
        rv = self.testclient.post('/auth/login', base_url=self.base_url, content_type='application/json', 
                  data=json.dumps(data), headers=[basic_auth_header("thesis@finish.it", "never")])
        assert 'token' in rv.data
        assert '201' in rv.data
        assert 'set-cookie' in rv.headers
        match = re.search(r'\bexpires=([^;]+)', rv.headers['set-cookie'])
        assert match is not None
        rv = self.testclient.get('/auth/supersecret', base_url=self.base_url)
        self.assertIn('secret', rv.data)

    def testValidLoginWithoutDeviceInfo(self):
        self.setupUserAccounts()
        data = None
        rv = self.testclient.post('/auth/login', base_url=self.base_url, content_type='application/json', 
                  data=json.dumps(data), headers=[basic_auth_header("thesis@finish.it", "never")])
        assert '400' in rv.data

    def testInvalidLoginWithIncorrectPassword(self):
        self.setupUserAccounts()
        rv = self.testclient.post('/auth/login', base_url=self.base_url, 
                  data=dict(device_info="flask.test_client"),
                  headers=[json_content_header, basic_auth_header("thesis@finish.it", "done")])
        assert '401' in rv.data

    def testInvalidLoginWithInvalidUsername(self):
        self.setupUserAccounts()
        rv = self.testclient.post('/auth/login', base_url=self.base_url,
                  data=dict(device_info="flask.test_client"),
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
                 assert 'identity.name' not in flask.session
                 self.fail('identity.name should not be found in the session')
             except RuntimeError:
                 pass 
             rv = c.get('/auth/supersecret', base_url=self.base_url, headers=[('X-Auth-Token',token)])
             assert 'identity.name' in flask.session
             assert flask.session['loaded_from'] == 'couchdb'
             rv = c.get('/auth/supersecret', base_url=self.base_url, headers=[('X-Auth-Token',token)])
             self.assertIn('secret', rv.data)
             assert flask.session['loaded_from'] == 'memcached'
             rv = c.get('/auth/logout', base_url=self.base_url, headers=[('X-Auth-Token',token)])
             assert '200' in rv.data
             assert flask.session['identity.name'] == 'anon'
             rv = c.get('/auth/supersecret', base_url=self.base_url, headers=[('X-Auth-Token',token)])
             assert '403' in rv.data

    def testInvalidTokenAuthentication(self):
        token = 'invalid-token'
        rv = self.testclient.get('/auth/supersecret', base_url=self.base_url, headers=[('X-Auth-Token',token)])
        self.assertNotIn('secret', rv.data)
        self.assertIn('403', rv.data)
        assert 'set-cookie' not in rv.headers

    def testNonProtectedEndPoint(self):
        rv = self.testclient.get('/auth/notsosecret', base_url=self.base_url)
        assert 'set-cookie' not in rv.headers
        

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuthenticationTests, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
