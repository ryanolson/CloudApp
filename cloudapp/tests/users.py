# -*- coding: utf-8 -*-
import unittest
from cloudapp.tests.framework import TestingFramework

from cloudapp import BaseUser as User
from cloudapp.authentication import Session
from flask.ext.couchdb import MD5Type, make_safe_json

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
        self.assertNotEqual(user.password, MD5Type.generate('pass1'))
        self.assertTrue(user.challenge_password('pass1'))

    def testSetPassword(self):
        user = User(email='user1@gmail.com')
        user.password = 'pass1'
        self.assertNotEqual(user.password, MD5Type.generate('pass1'))
        self.assertTrue(user.challenge_password('pass1'))

    def testUserWithInvalidEmail(self):
        user = User()
        user.email = 'invalid@email'
        self.assertRaises( Exception, user.store, self.db)

    def testIncompleteUserNoPassword(self):
        user = User(email="test@gmail.com")
        self.assertRaises( Exception, user.store, self.db)

    def testValidUser(self):
        user = User(email='ryan.olson@gmail.com', password=MD5Type.generate('secret'))
        self.assertTrue(user.challenge_password(MD5Type.generate('secret')))
        user.store(self.db)
        self.assertEqual(self.db[user.id][u'email'], u'ryan.olson@gmail.com')
        self.assertEqual(user.id, 'ryanolson@gmail.com')

    def testRoles(self):
        # TODO - broken
        return
        user = User(email='ryan.olson@gmail.com', password=MD5Type.generate('secret'))
        user.store(self.db)
        self.assertEqual(user.id, u'ryanolson@gmail.com')
        self.assertEqual(self.db[user.id][u'email'], u'ryan.olson@gmail.com')
        json = make_safe_json(User,user,'mysessions')
        assert 'password' not in json
        assert 'token' not in json
        assert 'email' in json
        assert 'created_on' in json
        assert self.db[user.id]['password'] is not None
        u2 = User.load(self.db, user.id)
        self.assertTrue(u2.challenge_password(MD5Type.generate('secret')))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UserTestCases, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
