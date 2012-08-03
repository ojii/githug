# -*- coding: utf-8 -*-
import base64
from functools import update_wrapper
import urllib
from flask import session, redirect, url_for, request, abort
import json
import urlparse
import os
import requests


class GithubAuth(object):
    session_suffix_username = 'username'
    session_suffix_state = 'state'
    session_suffix_url = 'url'
    default_redirect = '/'

    def __init__(self, client_id, client_secret, session_key_prefix, model, username_field,
                 access_token_field, admin_field, login_view_name):
        self.client_id = client_id
        self.client_secret = client_secret
        self.session_key_prefix = session_key_prefix
        self.username_session_key = '%s%s' % (self.session_key_prefix, self.session_suffix_username)
        self.state_session_key = '%s%s' % (self.session_key_prefix, self.session_suffix_state)
        self.url_session_key = '%s%s' % (self.session_key_prefix, self.session_suffix_url)
        self.model = model
        self.username_field = username_field
        self.access_token_field = access_token_field
        self.admin_field = admin_field
        self.login_view_name = login_view_name
        self.access_token_url = 'https://github.com/login/oauth/access_token'
        self.login_url = 'https://github.com/login/oauth/authorize'
        self.user_url = 'https://api.github.com/user'
        self.requests_session = requests.session()

    def access_token_to_data(self, access_token):
        response = self.requests_session.get(self.user_url, params={'access_token': access_token})
        return {'user': json.loads(response.content), 'access_token': access_token}

    def code_to_access_token(self, code):
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            }
        response = self.requests_session.post(self.access_token_url, data=data)
        return urlparse.parse_qs(response.content)['access_token'][0]

    def get_data_from_code(self, code):
        access_token = self.code_to_access_token(code)
        return self.access_token_to_data(access_token)

    def login(self):
        if self.get_user():
            return redirect(url_for(self.redirect_url_name))
        state = base64.b64encode(os.urandom(20))
        session[self.state_session_key] = state
        params = urllib.urlencode({
            'client_id': self.client_id,
            'state': state,
            })
        url = '%s?%s' % (self.login_url, params)
        return redirect(url)

    def logout(self):
        if self.username_session_key in session:
            del session[self.username_session_key]

    def auth(self):
        code = request.args.get('code', None)
        if not code:
            abort(400)
        state = request.args.get('state', None)
        if not state or self.state_session_key not in session or state != session[self.state_session_key]:
            abort(400)
        del session[self.state_session_key]
        data = self.get_data_from_code(code)
        if not data:
            abort(400)
        username = data['user']['login']
        session[self.username_session_key] = username
        user = self.build_user(data)
        user.save()
        url = session.pop(self.url_session_key, self.default_redirect)
        return redirect(url)

    def build_user(self, data):
        try:
            user = self.model.objects.get(**{self.username_field: data['user']['login']})
        except self.model.DoesNotExist:
            user = self.model(**{self.username_field: data['user']['login']})
        setattr(user, self.access_token_field, data['access_token'])
        return user

    def login_required(self, view):
        def _decorate(*args, **kwargs):
            if self.get_user():
                return view(*args, **kwargs)
            else:
                session[self.url_session_key] = request.path
                return redirect(url_for(self.login_view_name))
        update_wrapper(_decorate, view)
        return _decorate

    def admin_required(self, view):
        def _decorate(*args, **kwargs):
            user = self.get_user()
            if user and getattr(user, self.admin_field, False):
                return view(*args, **kwargs)
            else:
                session[self.url_session_key] = request.path
                return redirect(url_for('login'))
        update_wrapper(_decorate, view)
        return _decorate

    def get_user(self):
        username = session.get(self.username_session_key, None)
        if not username:
            return None
        try:
            user = self.model.objects.get(**{self.username_field: username})
        except self.model.DoesNotExist:
            return None
        return user
