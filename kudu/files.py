import os
import tempfile
import zipfile
from datetime import datetime

import requests

from kudu import logger
from kudu.exceptions import FileNotFound, BranchNotPermitted
from kudu.exceptions import NotFound


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


def deploy_file(backend, deployment, active_branch):
    if isinstance(deployment['id'], dict):
        if active_branch not in deployment['id']:
            raise BranchNotPermitted('Skipping a deployment because this branch is not permitted: %s' % active_branch)

        deployment['id'] = deployment['id'][active_branch]

    file_data = get_file(backend, deployment['id'])
    file_path = deployment['path']

    if os.path.isdir(file_path):
        logger.log('Create %s' % file_data['filename'])

        if file_data['category']:
            file_path = make_zip(file_path, file_data['filename'])
        else:
            file_path = make_ui(file_path, file_data['filename'])

    logger.log('Upload file %s' % file_data['id'])

    upload_file(
        backend,
        file_data['id'],
        file_path
    )

    save_file(
        backend, file_data['id'],
        body=deployment.get('body'),
        keywords=deployment.get('keywords'),
        creation_time=datetime.utcnow().isoformat()
    )


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
