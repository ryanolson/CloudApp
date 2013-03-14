# -*- coding: utf-8 -*-
import unittest
from cloudapp.tests.framework import TestingFramework
from warnings import warn
from flask import current_app

class TestMemcached(TestingFramework):

    def testMemCached(self):
        with self.app.test_request_context('/'):
             self.app.preprocess_request()
             assert current_app.cache is not None

def suite():
    suite = unittest.TestSuite()
    try:
       from werkzeug.contrib.cache import MemcachedCache
       cache = MemcachedCache(['127.0.0.1:11211'])
       suite.addTest(unittest.makeSuite(TestMemcached, 'test'))
    except RuntimeError:
       warn("MemcachedCache can not be loaded; skipping tests.", RuntimeWarning)
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
