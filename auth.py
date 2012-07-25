# -*- coding: utf-8 -*-
from functools import update_wrapper
import urllib
from flask import session, redirect, url_for, request
import json
import urlparse
import requests


class GithubAuth(object):
    def __init__(self, client_id, client_secret, session_key, redirect_url_name, model, username_field,
                 access_token_field, admin_field):
        self.client_id = client_id
        self.client_secret = client_secret
        self.session_key = session_key
        self.redirect_url_name= redirect_url_name
        self.model = model
        self.username_field = username_field
        self.access_token_field = access_token_field
        self.admin_field = admin_field
        self.access_token_url = 'https://github.com/login/oauth/access_token'
        self.login_url = 'https://github.com/login/oauth/authorize'
        self.user_url = 'https://api.github.com/user'

    def access_token_to_data(self, access_token):
        response = requests.get(self.user_url, params={'access_token': access_token})
        return {'user': json.loads(response.content), 'access_token': access_token}

    def code_to_access_token(self, code):
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            }
        response = requests.post(self.access_token_url, data=data)
        return urlparse.parse_qs(response.content)['access_token'][0]

    def get_data_from_code(self, code):
        access_token = self.code_to_access_token(code)
        return self.access_token_to_data(access_token)

    def login(self):
        if self.get_user():
            return redirect(url_for(self.redirect_url_name))
        params = urllib.urlencode({
            'client_id': self.client_id,
            })
        url = '%s?%s' % (self.login_url, params)
        return redirect(url)

    def auth(self):
        code = request.args.get('code', None)
        if code:
            data = self.get_data_from_code(code)
            if data:
                username = data['user']['login']
                session[self.session_key] = username
                try:
                    user = self.model.objects.get(**{self.username_field: data['user']['login']})
                except self.model.DoesNotExist:
                    user = self.model(**{self.username_field: data['user']['login']})
                setattr(user, self.access_token_field, data['access_token'])
                user.save()
                return redirect(url_for(self.redirect_url_name))
        return redirect('/')

    def login_required(self, view):
        def _decorate(*args, **kwargs):
            if self.get_user():
                return view(*args, **kwargs)
            else:
                return redirect(url_for('login'))
        update_wrapper(_decorate, view)
        return _decorate

    def admin_required(self, view):
        def _decorate(*args, **kwargs):
            user = self.get_user()
            if user and getattr(user, self.admin_field, False):
                return view(*args, **kwargs)
            else:
                return redirect(url_for('login'))
        update_wrapper(_decorate, view)
        return _decorate

    def get_user(self):
        username = session.get(self.session_key, None)
        if not username:
            return None
        # legacy:
        if isinstance(username, dict):
            data = username
            username = data['user']['login']
            session[self.session_key] = username
            try:
                user = self.model.objects.get(**{self.username_field: username})
            except self.model.DoesNotExist:
                user = self.model(**{self.username_field: username})
            setattr(user, self.access_token_field, data['access_token'])
            user.save()
        else:
            try:
                user = self.model.objects.get(**{self.username_field: username})
            except self.model.DoesNotExist:
                user = self.model(**{self.username_field: username})
                user.save()
        return user
