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

import re, string, datetime, urllib, hashlib
from cloudapp import public
from flask import current_app, g, session
from flask.ext.couchdb import *
from flask.ext.principal import AnonymousIdentity

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
(CouchDB reserves _'ed attributes), so we use the "print_name" feature
so that the value of the _password field will be serialized to "password"
with any of the schematics.serialize routines.

This leaved one headache.  We don't want to rehash the value of password
when loading the Document from CouchDB.  Thus we have the condition in 
__init__ that ignores the "password" keyword if "_rev" is present.

"""

gmail = re.compile('[%s]' % re.escape(string.punctuation))
 
def _remove_dots_from_gmail_username(email):
    rv = email
    if "@gmail.com" in rv:
       username = rv.split('@')[0]
       username = gmail.sub('',username)
       rv = "{0}@gmail.com".format(username)
    return rv

@public
class Session(Document):
    user_id = StringType(required=True)
    auth_type = StringType(choices=['web-token','api-token','facebook','google'])
    created_on = DateTimeType(default=datetime.datetime.utcnow)
    device_info = DictType(default=None)
    class Options:
       roles = {
          'mysessions': blacklist('token')
       }

    web_token = ViewDefinition('auth','web-token', '''\
      function(doc) {
        if(doc.doc_type == "Session" && doc.auth_type == 'web-token') {
           emit(doc.user_id, doc);
        }
      ''')

    @property
    def token(self):
        if self.id is None:
           raise RuntimeError("Session Token (doc._id) is None")
        return self.id

@public
class BaseUser(Document):

    email = EmailType(required=True)
    last_name = StringType()
    first_name = StringType()
    roles = ListType(StringType())
    email_verified = BooleanType(default=False)
    _password = MD5Type(required=True,print_name="password")
    fb_token = StringType()

    class Options:
        roles = {
           'me': blacklist('_password','sessions'),
           'mysessions': blacklist('_password')
        }

    ##
    ## Views
    ##
    # doc.sessions.forEach(function (session) {

    token = ViewDefinition('auth', 'token', '''\
      function(doc) {
        if(doc.doc_type == "Session") {
          emit(doc._id, doc);
        }
      }''',wrapper=Session._wrap_row)


    def __init__(self, *args, **kwargs):
        kwargs['doc_type'] = 'User'
        super(BaseUser, self).__init__(*args, **kwargs)
        if 'password' in kwargs and '_rev' not in kwargs:
           self._password = self._salted_password(kwargs['password'])

    def _get_password(self):
        return self._password

    def _set_password(self,passwd):
        self._password = self._salted_password(passwd)

    password = property(_get_password, _set_password)
    
    def challenge_password(self,passwd):
        if self.password == self._salted_password(passwd): return True
        return False

    def create_session(self, device_info=None, verify_email=False, *args, **kwargs):
        if self.id is None: return None
        if not verify_email or (verify_email and self.email_verified):
           session = Session(user_id=self.id, device_info=device_info).store()
           if session is None:
              raise RuntimeError("failed to create an authentication session")
           return str(session.token)
        return None

    def gravatar_url(self,size=40,default=None):
        if default is None:
           default = 'mm'
        gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(self.email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
        return gravatar_url

#   def remove_session(self, token):
#       for s in range(len(self.sessions)):
#           session = self.sessions[s]
#           if str(session.token) == token:
#              del self.sessions[s]
#              self.store()

    @classmethod
    def load(cls, id, db=None):
        return super(BaseUser,cls).load(_remove_dots_from_gmail_username(id),db=db)

    def store(self, db=None, validate=True):
        if self.id is None and self.email is not None:
           self.id = _remove_dots_from_gmail_username(self.email)
        return super(BaseUser,self).store(db=db,validate=validate)

    def _salted_password(self, passwd):
        s = "salt+{}".format(passwd)
        return MD5Type.generate(s)


@public
def validate_token(token):
    if token is None: return False
    if current_app.cache is not None:
       if current_app.cache.get(token) is not None:
          return True 
    auth_session = Session.load(token)
    if auth_session:
       return True
    return False


@public
def logout():
    assert g.identity
    if current_app.cache is not None:
       current_app.cache.delete(g.identity.name)
    g.identity = AnonymousIdentity()
    session.pop('identity.name', None)
    session.pop('identity.auth_type', None)
    session.modified = True

