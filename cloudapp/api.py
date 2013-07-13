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
from cloudapp import public

@public
def Blueprint(name, **kwargs):
    from flask import Blueprint
    from werkzeug.exceptions import default_exceptions
    from cloudapp.authentication.decorators import load_user
    error_if_exists = kwargs.pop('subdomain', None)
    if error_if_exists:
       raise RuntimeError("[cloudapp_api] Blueprint: subdomain is not an allowed keyword")
    url_prefix = kwargs.get('url_prefix', '')
    kwargs['url_prefix'] = '/api/v1' + url_prefix
    bp = Blueprint(name, __name__, **kwargs)
    bp.before_request(load_user)
    bp.before_request(_process_request_json)
    for code in default_exceptions.iterkeys():
        if code >= 500: continue
        @bp.errorhandler(code)
        def errorhandler(code):
            return _json_errorhandler(code)
    return bp


def _process_request_json():
    from flask import request, json, g
    g.json = None
    if request.data:
       try:
          g.json = json.loads(request.data)
       except:
          env = Envelope(400)
          env.add_meta('error_message','expected a valid json')
          return env.send()

def _json_errorhandler(ex):
    from flask import jsonify
    from werkzeug.exceptions import HTTPException
    response = jsonify( meta = { 'error_message': str(ex), 'code': ex.code })
    response.status_code = (ex.code
                            if isinstance(ex, HTTPException)
                            else 500)
    return response


@public
class Envelope:
    def __init__(self, code=200):
        self.payload = { }
        self.payload['meta'] = { 'code': code }
        self.payload['data'] = [ ]
        self.payload['pagination'] = { }

    def add_meta(self,key,value):
        self.payload['meta'][key] = value

    def add_data(self,value):
        self.payload['data'].append(value)

    def send(self):
        from flask import jsonify
        if 'data' in self.payload:
           if len(self.payload['data']) == 0:
              del(self.payload['data'])
        if 'pagination' in self.payload:
           if len(self.payload['pagination'].keys()) == 0:
              del(self.payload['pagination'])
        response = jsonify(self.payload)
        response.status_code = self.payload['meta']['code']
        return response

