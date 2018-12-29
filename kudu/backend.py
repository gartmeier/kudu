import os
import tempfile
import urllib

import requests

from kudu.exceptions import NotFound, NotAuthorized, InvalidAuth


def _res(res):
    if res.status_code == 400:
        raise NotFound()
    elif res.status_code == 401:
        raise NotAuthorized()

    return res.json()


class Backend(object):
    url = 'http://0.0.0.0:8000'
    token = None

    def get_token_file(self):
        filename = urllib.quote(self._url(''), '')
        return os.path.join(tempfile.gettempdir(), 'pitauth' + filename)

    def restore_token(self):
        path = self.get_token_file()
        if os.path.isfile(path):
            with open(path, 'r') as fh:
                self.token = fh.read()

        # validate
        if self.token:
            try:
                self.get('/apps/?limit=1')
            except NotAuthorized:
                self.token = None

        return self.token is not None

    def save_token(self):
        if self.token:
            path = self.get_token_file()
            with open(path, 'w') as fh:
                fh.write(self.token)

    def remove_token(self):
        os.remove(self.get_token_file())

    def authenticate(self, username, password):
        try:
            res = self.post('/auth/user/', data={
                'username': username,
                'password': password
            })
            self.token = res.get('token')
        except NotFound:
            raise InvalidAuth('Invalid username or password')

        self.save_token()

    def _url(self, path):
        return self.url + path

    def _auth(self, kwargs):
        if self.token:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['Authorization'] = 'Token %s' % self.token

        return kwargs

    def get(self, path, **kwargs):
        return _res(requests.get(self._url(path), **self._auth(kwargs)))

    def post(self, path, **kwargs):
        return _res(requests.post(self._url(path), **self._auth(kwargs)))

    def put(self, path, **kwargs):
        return _res(requests.put(self._url(path), **self._auth(kwargs)))

    def patch(self, path, **kwargs):
        return _res(requests.patch(self._url(path), **self._auth(kwargs)))
