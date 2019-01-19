import os
import tempfile
import urllib
import zipfile
from datetime import datetime
from getpass import getpass

import requests

from kudu.exceptions import FileNotFound, NotFound, NotAuthorized, InvalidAuth
from kudu.providers.base import SftpProvider


def make_zip(root_dir, filename):
    base_dir = os.path.splitext(filename)[0]

    zip_file = os.path.join(tempfile.tempdir, filename)
    zip_handler = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)

    save_cwd = os.getcwd()
    os.chdir(root_dir)

    try:
        for root, dirs, files in os.walk('.'):
            for file in files:
                arcfile = file

                if root == '.' and file == 'thumbnail.png':
                    arcfile = base_dir + '.png'

                zip_handler.write(os.path.join(root, file), os.path.join(base_dir, root, arcfile))
    finally:
        os.chdir(save_cwd)

    return zip_file


def make_ui(root_dir, filename):
    base_dir = os.path.splitext(filename)[0]

    zip_file = os.path.join(tempfile.tempdir, filename)
    zip_handler = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)

    save_cwd = os.getcwd()
    os.chdir(root_dir)

    try:
        for root, dirs, files in os.walk('.'):
            root_dirs = root.split(os.path.sep)

            if len(root_dirs) > 1 and root_dirs[1] == 'interface':
                root_dirs[1] = base_dir

            arcroot = os.path.sep.join(root_dirs)

            for file in files:
                zip_handler.write(os.path.join(root, file), os.path.join(arcroot, file))
    finally:
        os.chdir(save_cwd)

    return zip_file


def _res(res):
    if res.status_code == 400:
        raise NotFound()
    elif res.status_code == 401:
        raise NotAuthorized()

    return res.json()


class PitcherFileProvider(object):
    name = 'pitcherfile'

    api_url = 'https://nyala.pitcher.com'
    api_token = None

    def push(self, file_filename, file_path, logger=None):
        # TODO move to config and pass api_token as argument
        if not self.restore_token():
            username = raw_input("Username for %s: " % self.api_url)
            password = getpass("Password for %s: " % self.api_url)
            self.authenticate(username, password)

        files = self.get_files(filename=file_filename)

        if len(files) == 0:
            raise FileNotFound('invalid filename \'{filename}\''.format(filename=file_filename))

        file = files[0]

        if os.path.isdir(file_path):
            if logger:
                # TODO Compressing objects: 100% 66/66, done.
                logger.info('Compressing objects')

            if file['category']:
                file_path = make_zip(file_path, file['filename'])
            else:
                file_path = make_ui(file_path, file['filename'])

        if logger:
            # TODO Writing objects: 100% 90.06 KiB, done.
            logger.info('Writing objects')

        self.upload_file(file['id'], file_path)
        self.save_file(file_id=file['id'], creation_time=datetime.utcnow().isoformat())

    def deploy(self, file_id, file_path, body=None, keywords=None, logger=None):
        # TODO move to config and pass api_token as argument
        if not self.restore_token():
            username = raw_input("Username for %s: " % self.api_url)
            password = getpass("Password for %s: " % self.api_url)
            self.authenticate(username, password)

        file = self.get_file(file_id)

        if os.path.isdir(file_path):
            if logger:
                # TODO Compressing objects: 100% 66/66, done.
                logger.info('Compressing objects')

            if file['category']:
                file_path = make_zip(file_path, file['filename'])
            else:
                file_path = make_ui(file_path, file['filename'])

        if logger:
            # TODO Writing objects: 100% 90.06 KiB, done.
            logger.info('Writing objects')

        self.upload_file(file_id, file_path)
        self.save_file(file_id=file_id, body=body, keywords=keywords, creation_time=datetime.utcnow().isoformat())

    def get_files(self, **kwargs):
        return self.get('/files/', params=kwargs)

    def get_file(self, file_id):
        try:
            return self.get('/files/{file_id}/'.format(file_id=file_id))
        except NotFound:
            raise FileNotFound('invalid id \'{file_id}\''.format(file_id=file_id))

    def upload_file(self, file_id, path):
        res = self.get('/files/{file_id}/upload-url/'.format(file_id=file_id))
        requests.put(res, data=open(path, 'r'))

    def save_file(self, file_id, body=None, keywords=None, creation_time=None):
        file_json = {}

        if body is not None:
            file_json['body'] = body

        if keywords is not None:
            file_json['keywords'] = keywords

        if creation_time is not None:
            file_json['creationTime'] = creation_time

        self.patch('/files/{file_id}/'.format(file_id=file_id), json=file_json)

    def get_token_file(self):
        filename = urllib.quote(self._url(''), '')
        return os.path.join(tempfile.gettempdir(), 'pitauth' + filename)

    def restore_token(self):
        if not self.api_token:
            path = self.get_token_file()
            if os.path.isfile(path):
                with open(path, 'r') as fh:
                    self.api_token = fh.read()

            # validate
            if self.api_token:
                try:
                    self.get('/apps/?limit=1')
                except NotAuthorized:
                    self.api_token = None

        return self.api_token

    def save_token(self):
        if self.api_token:
            path = self.get_token_file()
            with open(path, 'w') as fh:
                fh.write(self.api_token)

    def remove_token(self):
        os.remove(self.get_token_file())

    def authenticate(self, username, password):
        try:
            res = self.post('/auth/user/', data={
                'username': username,
                'password': password
            })
            self.api_token = res.get('token')
        except NotFound:
            raise InvalidAuth('Invalid username or password')

        self.save_token()

    def _url(self, path):
        return self.api_url + path

    def _auth(self, kwargs):
        if self.api_token:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['Authorization'] = 'Token %s' % self.api_token

        return kwargs

    def get(self, path, **kwargs):
        return _res(requests.get(self._url(path), **self._auth(kwargs)))

    def post(self, path, **kwargs):
        return _res(requests.post(self._url(path), **self._auth(kwargs)))

    def put(self, path, **kwargs):
        return _res(requests.put(self._url(path), **self._auth(kwargs)))

    def patch(self, path, **kwargs):
        return _res(requests.patch(self._url(path), **self._auth(kwargs)))


class PitcherFileDeploymet(object):
    provider = PitcherFileProvider()

    def __init__(self, file_id, body, keywords, path, logger):
        self.file_id = file_id
        self.body = body
        self.keywords = keywords
        self.path = path
        self.logger = logger

    def deploy(self):
        self.provider.deploy(
            self.file_id, self.path,
            body=self.body, keywords=self.keywords,
            logger=self.logger)


class SftpDeployment(object):
    provider = SftpProvider()

    def __init__(self, address, username, password=None, remote_path=None, local_path=None, files=None, logger=None):
        self.address = address
        self.username = username
        self.password = password
        self.remote_path = remote_path
        self.local_path = local_path
        self.files = files
        self.logger = logger

    def deploy(self):
        self.provider.deploy(
            self.address, self.username, password=self.password,
            remote_path=self.remote_path, local_path=self.local_path,
            files=self.files, logger=self.logger)


class PitcherZeroProvider(SftpProvider):
    name = 'pitcherzero'
