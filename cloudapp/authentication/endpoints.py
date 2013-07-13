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
from __future__ import absolute_import
from flask import request, g, current_app, abort
from flask.ext.principal import Identity, AnonymousIdentity, identity_changed
from cloudapp.api import Blueprint, Envelope
from cloudapp.permissions import valid_user

#rom cloudapp.authentication.decorators import requires_login
from .decorators import requires_login
#rom cloudapp.authentication.models import Session
from .models import Session

api = Blueprint('cloudapp_api', url_prefix='/auth' )

@api.route('/login',methods=['POST'])
@requires_login
def login():
    return get_or_creat_api_key( g.user )

@api.route('/signup', methods=['POST'])
def signup():
    if request.json is None: abort(400)
    if 'user' not in request.json: abort(400)
    if 'email_verified' in request.json['user']:
       del request.json['user']['email_verified']
    try:    
       user = g.User.wrap(request.json['user'])
       user.store()
       return get_or_creat_api_key( user )
    except:
       abort(400)

@api.route('/logout')
@valid_user.require(http_exception=403)
def logout():
    session = Session.load( g.identity.id )
    g.couch.db.delete( session )
    if current_app.cache is not None:
       current_app.cache.delete( g.identity.id )
    g.user = None
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    return Envelope(200).send()

@api.route('/tokens')
@valid_user.require(http_exception=403)
def getTokens():
    abort(400)

def get_or_creat_api_key(user):
    if request.json is None: abort(400)
    if 'device_info' not in request.json: abort(400)
    device_info = request.json['device_info']
    verify_email = current_app.config.get('VERIFY_EMAIL', False)
    token = user.create_session(device_info, verify_email)
    assert token is not None
    # todo - handle the case where VERIFY_EMAIL is true
    identity_changed.send(current_app._get_current_object(), identity=Identity(token, auth_type='token'))
    envelope = Envelope(201)
    envelope.add_meta('token', token)
    envelope.add_data( user.serialize('basic_info') )
    return envelope.send()

