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
from urlparse import urlparse, urljoin
from flask import Blueprint, request, redirect, render_template, g, url_for, current_app
from flask.ext.principal import Identity, identity_changed
from flask.ext.wtf import Form, TextField, PasswordField, HiddenField, DataRequired
#from schematics.wtf import model_form


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

class RedirectForm(Form):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))

#class Login(Model):
#    email = EmailType(required=True)
#    password = StringType(min_length=6, max_length=32)
# -wtf.model_form- BaseLoginForm = model_form(Login, base_class=RedirectForm, field_args=dict(password=dict(password=True)))

class BaseLoginForm(Form):
    email = TextField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])

 
class LoginForm(BaseLoginForm):

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

    def validate(self):
        rv = super(LoginForm,self).validate()
        if not rv:
            return False

        user = g.User.load(self.email.data)
        if user is None:
            self.email.errors.append('Unknown email address')
            return False

        if not user.challenge_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False

        identity_changed.send(current_app._get_current_object(), identity=Identity(user.id, auth_type='web-token'))
        return True

#@auth.route('/login', methods=['POST','GET'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
       return redirect( url_for("www.index") )
       return login_form.redirect("www.index")
    return render_template("signin.html", form=login_form)

#@auth.route('/logout')
def logout():
    from .models import logout as models_logout
    models_logout()
    return redirect(url_for('www.index'))
