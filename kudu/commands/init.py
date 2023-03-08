import click
import os
import json
from kudu.api import request
from kudu.config import write_config


@click.command()
@click.pass_context
def init(ctx):
    if click.confirm('Would you like to create a new file?'):
        app_id = click.prompt('Instance ID', type=int)
        file_body = click.prompt('File Body')
        file_id = create_file(ctx.obj['token'], app_id, file_body, download_url='https://admin.pitcher.com/downloads/Pitcher%20HTML5%20Folder.zip')
    else:
        file_id = validate_file(
            click.prompt('File ID', type=int), ctx.obj['token']
        )

    write_config({'file_id': file_id})


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

    res = request(
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


def validate_file(file_id, token):
    api_res = request('get', '/files/%d/' % file_id, token=token)

    if api_res.status_code != 200:
        click.echo('Invalid file', err=True)
        exit(1)

    if api_res.json().get('category') not in ('zip', 'presentation', ''):
        click.echo('Invalid category', err=True)
        exit(1)

    return file_id
