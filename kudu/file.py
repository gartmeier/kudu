import os
import click
import os

from collections import namedtuple
from datetime import datetime
import time

from kudu.api import request as api_request
from kudu.mkztemp import NameRule, mkztemp

CategoryRule = namedtuple('crule', ('category', 'rule'))


CATEGORY_RULES = (
    CategoryRule('',
                 NameRule((r'^interface', r'(.+)'), ('{base_name}', '{0}'))),
    CategoryRule(('presentation', 'zip'),
                 NameRule(r'^thumbnail.png', '{base_name}.png')),
    CategoryRule(('presentation', 'zip'),
                 NameRule(r'(.+)', ('{base_name}', '{0}'))),
) # yapf: disable

def upload_file(token, app_id, file_body, file_data, file_name, file_id = None):
    multipart_form_data = {
        'app': (None, app_id),
        'body': (None, file_body),
        'file': (
            file_name,
            file_data,
            'application/octet-stream'
        ),
        'filename': (None, file_name)
    }

    url = '/files/%s' % file_id + '/' if file_id else '/files/'
    return handle_file_create_response(api_request(
        'patch' if file_id else 'post',
        url,
        files=multipart_form_data,
        token=token
    ))

def upload_file_from_url(token, app_id, file_body, download_url):
    return handle_file_create_response(api_request(
        'post',
        '/files/',
        json={
            'app':
                app_id,
            'body':
                file_body,
            'downloadUrl': 
                download_url
        },
        token=token
    ))

def handle_file_create_response(res):
    resJson = res.json()

    if res.status_code != 201 and res.status_code != 200:
        if resJson.get('app'):
            click.echo('Invalid instance', err=True)
        else:
            click.echo('Unknown error', err=True)
        exit(1)

    return resJson.get('id')



def update_file_metadata(token, file_id):
    url = '/files/%d/' % file_id
    json = {
        'creationTime': datetime.utcnow().isoformat(),
        'metadata': get_metadata_with_github_info(token, file_id)
    }
    api_request('patch', url, json=json, token=token)


def get_file_data(filename, category, path = None):
    base_name, _ = os.path.splitext(filename)

    if path is None or os.path.isdir(path):
        rules = [c.rule for c in CATEGORY_RULES if category in c.category]
        fp, _ = mkztemp(base_name, root_dir=path, name_rules=rules)
        data = os.fdopen(fp, 'r+b')
    else:
        data = open(path, 'r+b')

    return data

def get_metadata_with_github_info(token, file_id):
    # first get existing metadata then modify it
    url = '/files/%d/' % file_id
    response = api_request('get', url, token).json()
    metadata = response.get('metadata', {})

    # NOT losing repo info for non-github deployments
    current_repo_info = metadata.get('GITHUB_REPOSITORY', 'not_available') 
    metadata['GITHUB_REPOSITORY'] = os.environ.get('GITHUB_REPOSITORY', current_repo_info)

    # losing commit SHA and run id info for non-github deployments
    metadata['GITHUB_SHA'] = os.environ.get('GITHUB_SHA', 'not_available')
    metadata['GITHUB_RUN_ID'] = os.environ.get('GITHUB_RUN_ID', 'not_available')

    return metadata