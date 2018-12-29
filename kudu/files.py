import requests

from kudu.exceptions import FileNotFound, NotFound


def get_files(backend, **kwargs):
    return backend.get('/files/', params=kwargs)


def get_file(backend, file_id):
    try:
        return backend.get('/files/{file_id}/'.format(file_id=file_id))
    except NotFound:
        raise FileNotFound('invalid id \'{file_id}\''.format(file_id=file_id))


def upload_file(backend, file_id, path):
    res = backend.get('/files/{file_id}/upload-url/'.format(file_id=file_id))
    requests.put(res, data=open(path, 'r'))


def save_file(backend, file_id, body=None, keywords=None, creation_time=None):
    file_json = {}

    if body is not None:
        file_json['body'] = body

    if keywords is not None:
        file_json['keywords'] = keywords

    if creation_time is not None:
        file_json['creationTime'] = creation_time

    backend.patch('/files/{file_id}/'.format(file_id=file_id), json=file_json)
