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

import re, string, datetime, urllib, hashlib, uuid
from cloudapp import public
from flask import current_app, g, session
from flask.ext.principal import AnonymousIdentity

from flask.ext.couchdb import ViewDefinition
from flask.ext.couchdb.schematics_document import Document

from schematics.models import Model
from schematics.types import StringType, DateTimeType, UUIDType, EmailType, MD5Type, BooleanType
from schematics.types.compound import ListType, DictType, ModelType
from schematics.serialize import blacklist, whitelist
"""
BaseUser is the base class for a more general User class.  BaseUser
is designed to encapsulate all the basic authentication for the
User class.

BaseUser tests ModelType via the BaseUser.Session class.  This ModelType
tests an auto_fill fields and two fields with default options, one being
callable and the other being None.

BaseUser requires both the email and _password fields be valid.  BaseUser
also tests the ListType field using the Session ModelType as entries.

BaseUser also has a "hidden" field in _password.  The password
property uses the _get_password and _set_password for a getter/setter.
The setter automatically hashes the value passed with a salted string.
CouchDB will not let us save a field with the name "_password", 
(CouchDB reserves _'ed attributes), so we use the "serialized_name" feature
so that the value of the _password field will be serialized to "password"
with any of the schematics.serialize routines.

This leaved one headache.  We don't want to rehash the value of password
when loading the Document from CouchDB.  Thus we have the condition in 
__init__ that ignores the "password" keyword if "_rev" is present.

"""

def _remove_dots_from_gmail_username(email):
    gmail_regex = re.compile('[%s]' % re.escape(string.punctuation))
    rv = email
    if "@gmail.com" in rv:
       username = rv.split('@')[0]
       username = gmail_regex.sub('',username)
       rv = "{0}@gmail.com".format(username)
    return rv


class APIKey(Model):
    key = UUIDType(required=True)
    secret = UUIDType(required=True)

#--class APIKey(Document):
#--    user_id = StringType(required=True)
#--    secret = UUIDType(required=True)
#--    created_on = DateTimeType(default=datetime.datetime.utcnow)
#--    
#--    class Options:
#--       serialize_when_none = False
#--       roles = {
#--          'safe': blacklist('secret')
#--       }
#--
#--    web_token = ViewDefinition('auth','user_key', '''\
#--      function(doc) {
#--        if(doc.doc_type == "APIKey") {
#--           emit(doc.user_id, doc);
#--        }
#--      ''')
#--
#--    def __init__(self, **kwargs):
#--        if '_rev' not in kwargs:
#--           kwargs['_id'] = uuid.uuid4().hex
#--           kwargs['secret'] = uuid.uuid4()
#--        super(APIKey,self).__init__(**kwargs)
#--
#--    @property
#--    def key(self):
#--        if self.id is None:
#--           raise RuntimeError("Session Token (doc._id) is None")
#--        return self.id

@public
class BaseUser(Document):
    _password = MD5Type(required=True,serialized_name="password")
    email = EmailType(required=True)
    last_name = StringType()
    first_name = StringType()
    roles = ListType(StringType())
    apikey = ModelType(APIKey)

    class Options:
        serialize_when_none = False
        roles = {
           'safe': blacklist('_password')
        }

    ##
    ## Views
    ##
    # doc.sessions.forEach(function (session) {

    token = ViewDefinition('auth', 'apikey', '''\
      function(doc) {
        if(doc.doc_type == "User") {
          if(doc.apikey) {
             emit(doc.apikey.key, doc);
          }
        }
      }''')


    def __init__(self, **kwargs):
        kwargs['doc_type'] = 'User'
        if 'password' in kwargs and '_rev' not in kwargs:
           kwargs['password'] = self._salted_password(kwargs.pop('password'))
        super(BaseUser, self).__init__(**kwargs)

    def _get_password(self):
        return self._password

    def _set_password(self,passwd):
        self._password = self._salted_password(passwd)

    password = property(_get_password, _set_password)
    
    def _salted_password(self, passwd):
        s = "salt+{}".format(passwd)
        import hashlib
        return hashlib.md5(s).hexdigest()

    def challenge_password(self,passwd):
        if self._password == self._salted_password(passwd): return True
        return False

    @classmethod
    def load(cls, id, db=None):
        return super(BaseUser,cls).load(_remove_dots_from_gmail_username(id),db=db)

    def store(self, db=None, validate=True):
        if self.id is None and self.email is not None:
           self.id = _remove_dots_from_gmail_username(self.email)
        return super(BaseUser,self).store(db=db,validate=validate)

    def get_or_create_apikey(self, **kwargs):
        if self.apikey: return self.apikey
        self.apikey = APIKey(key=uuid.uuid4(), secret=uuid.uuid4())
        return self.apikey

    def gravatar_url(self,size=40,default=None):
        if default is None:
           default = 'mm'
        gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(self.email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
        return gravatar_url

def validate_token(token):
    if token is None: raise RuntimeError("invalid token")
    if current_app.cache is not None:
       if current_app.cache.get(token) is not None:
          pass

@public
def logout():
    assert g.identity
    if current_app.cache is not None:
       current_app.cache.delete(g.identity.id)
    g.identity = AnonymousIdentity()
    session.pop('identity.id', None)
    session.pop('identity.auth_type', None)
    session.modified = True

