# -*- coding: utf-8 -*-
from urlparse import urlparse, urljoin
from flask import Blueprint, request, redirect, render_template, g, url_for, current_app
from flask.ext.wtf import Form, HiddenField
from flask.ext.couchdb import Model, StringType, EmailType
from flask.ext.principal import Identity, identity_changed
from schematics.wtf import model_form

auth = Blueprint('cloudapp', __name__, url_prefix='/auth')

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

class Login(Model):
    email = EmailType(required=True)
    password = StringType(min_length=6, max_length=32)

BaseLoginForm = model_form(Login, base_class=RedirectForm, field_args=dict(password=dict(password=True)))

class LoginForm(BaseLoginForm):

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

    def validate(self):
        rv = super(LoginForm,self).validate()
        if not rv:
            return False

        user = g.User.load(self.email.data)
        if user is None:
            self.email.errors.append('Unknown username')
            return False

        if not user.challenge_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False

        identity_changed.send(current_app._get_current_object(), identity=Identity(user.id, auth_type='web-token'))
        return True

@auth.route('/login', methods=['POST','GET'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
       return redirect( url_for("www.index") )
       return login_form.redirect("www.index")
    return render_template("signin.html", form=login_form)

@auth.route('/logout')
def logout():
    from .models import logout as models_logout
    models_logout()
    return render_template(url_for('www.index'))
