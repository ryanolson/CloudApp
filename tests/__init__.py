# -*- coding: utf-8 -*-
import unittest
import authentication, users, memcached

def suite():
    suite = unittest.TestSuite()
    suite.addTest(authentication.suite())
    suite.addTest(users.suite())
    suite.addTest(memcached.suite())
    return suite

if __name__ == '__main__':
   unittest.main(defaultTest='suite')
