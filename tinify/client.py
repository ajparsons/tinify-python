# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import os
import platform
import requests
import requests.exceptions
import traceback

import tinify
from .errors import ConnectionError, Error

class Client(object):
    API_ENDPOINT = 'https://api.tinify.com'
    USER_AGENT = 'Tinify/{0} Python/{1} ({2})'.format(tinify.__version__, platform.python_version(), platform.python_implementation())

    def __init__(self, key, app_identifier=None):
        self.session = requests.sessions.Session()
        self.session.auth = ('api', key)
        self.session.headers = {
            'user-agent': self.USER_AGENT + ' ' + app_identifier if app_identifier else self.USER_AGENT,
        }
        self.session.verify = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cacert.pem')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.session.close()

    def request(self, method, url, body=None, header={}):
        url = url if url.lower().startswith('https://') else self.API_ENDPOINT + url
        params = {}
        if isinstance(body, dict):
            if body:
                params['json'] = body
        elif body:
            params['data'] = body

        try:
            response = self.session.request(method, url, **params)
        except requests.exceptions.Timeout as err:
            self.raise_from(ConnectionError('Timeout while connecting'), err)
        except Exception as err:
            self.raise_from(ConnectionError('Error while connecting: {0}'.format(err)), err)

        count = response.headers.get('compression-count')
        if count:
            tinify.compression_count = int(count)

        if response.ok:
            return response
        else:
            details = None
            try:
                details = response.json()
            except Exception as err:
                details = { 'message': 'Error while parsing response: {0}'.format(err), 'error': 'ParseError' }
            raise Error.create(details.get('message'), details.get('error'), response.status_code)

    @staticmethod
    def raise_from(err, cause):
        # Equivalent to `raise err from cause`, but also supported by Python 2
        if sys.version_info[0] >= 3 and cause is not None:
            err.__cause__ = cause
        raise err
