import os
import json
import click
import os

from collections import namedtuple
from datetime import datetime

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

def create_file(token, app_id, file_body, download_url = None, file_data= None):
    requestJSON = {
        'app':
            app_id,
        'body':
            file_body
    }

    if download_url:
        requestJSON['downloadUrl'] = download_url

    if file_data:
        files = {
            'json': (None, json.dumps(requestJSON), 'application/json'),
            'file': (os.path.basename(file_body), file_data, 'application/octet-stream')
        }

    res = api_request(
        'post',
        '/files/',
        files=files,
        token=token
    )

    resJson = res.json()

    if res.status_code != 201:
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