# -*- coding: utf-8 -*-
import unittest
from framework import TestingFramework

from flask import json
from cloudapp import BaseUser as User
from cloudapp.authentication import Session
from schematics.types import MD5Type
from schematics.exceptions import (
    BaseError, ValidationError, ConversionError,
    ModelValidationError, ModelConversionError,
)
import hashlib

class UserTestCases(TestingFramework):

    def testSessionCreation(self):
        # TODO - broken
        return
        token = Session().store(self.db)
        assert token.token is not None
        assert token.created_on is not None
        assert token.device_info is None

    def testPasswordSetterWithKeywordOnInitialization(self):
        user = User(email='user1@gmail.com',password='pass1')
        self.assertNotEqual(user.password, 'pass1')
        self.assertNotEqual(user.password, hashlib.md5('pass1').hexdigest())
        self.assertTrue(user.challenge_password('pass1'))

    def testSetPassword(self):
        user = User(email='user1@gmail.com')
        user.password = 'pass1'
        self.assertNotEqual(user.password, 'pass1')
        self.assertNotEqual(user.password, hashlib.md5('pass1').hexdigest())
        self.assertTrue(user.challenge_password('pass1'))

    def testUserWithInvalidEmail(self):
        user = User()
        user.email = 'invalid@email'
        self.assertRaises( ValidationError, user.store, self.db)

    def testIncompleteUserNoPassword(self):
        user = User(email="test@gmail.com")
        self.assertRaises( ValidationError, user.store, self.db)

    def testValidUser(self):
        user = User(email='ryan.olson@gmail.com', password='secret')
        self.assertTrue(user.challenge_password('secret'))
        user.store(self.db)
        self.assertEqual(self.db[user.id][u'email'], u'ryan.olson@gmail.com')
        self.assertEqual(user.id, 'ryanolson@gmail.com')

    def testRoles(self):
        # TODO - broken
        return
        user = User(email='ryan.olson@gmail.com', password='secret')
        user.store(self.db)
        self.assertEqual(user.id, u'ryanolson@gmail.com')
        self.assertEqual(self.db[user.id][u'email'], u'ryan.olson@gmail.com')
        json = json.dumps(user.serialize('mysessions'))
        assert 'password' not in json
        assert 'token' not in json
        assert 'email' in json
        assert 'created_on' in json
        assert self.db[user.id]['password'] is not None
        u2 = User.load(self.db, user.id)
        self.assertTrue(u2.challenge_password('secret'))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UserTestCases, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
