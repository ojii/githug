# -*- coding: utf-8 -*-

from flask import request, redirect

class ForceDomain(object):
    def __init__(self, app, domain):
        self.domain = domain
        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def init_app(self, app):
        """Configures the configured Flask app to enforce a specific domain."""
        app.before_request(self.redirect_to_domain)

    def redirect_to_domain(self):
        """Redirect incoming requests to a specific domain."""
        # Should we redirect?
        if request.host != self.domain:
            url = request.url.replace('//%s' % request.host, '//%s' % self.domain)
            return redirect(url)
