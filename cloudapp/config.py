# -*- coding: utf-8 -*-

class Config(object):
    DEBUG = False
    TESTING = False
    COUCHDB_SERVER = 'http://localhost:5984/'
    MEMCACHED_SERVERS = ['127.0.0.1:11211']
    VERIFY_EMAIL = False

class ProductionConfig(Config):
    pass

class DebugConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    DEBUG = False
    TESTING = True

