import os

import click

from kudu.api import authenticate, request
from kudu.config import write_global_config, write_config


@click.command()
@click.option('--path', default=os.getcwd(), type=click.Path(exists=True))
def init(path):
    username = click.prompt('Username for https://api.pitcher.com')
    password = click.prompt('Password for https://api.pitcher.com', hide_input=True)
    token = None

    try:
        token = authenticate(username, password)
    except ValueError:
        click.echo('Invalid username or password', err=True)
        exit(1)

    write_global_config({'username': username, 'password': password})

    if click.confirm('Would you like to create a new file?'):
        file_id = create_file(token)
    else:
        file_id = validate_file(click.prompt('File ID', type=int), token)

    write_config({'id': file_id}, path=path)


def create_file(token):
    app_id = click.prompt('Instance ID', type=int)
    file_body = click.prompt('File Body')

    res = request(
        'post', '/files/',
        json={
            'app': app_id,
            'body': file_body,
            'downloadUrl': 'https://admin.pitcher.com/downloads/Pitcher%20HTML5%20Folder.zip'
        },
        token=token
    )
    json = res.json()

    if res.status_code != 201:
        if json.get('app'):
            click.echo('Invalid instance', err=True)
        else:
            click.echo('Unknown error', err=True)
        exit(1)

    return json.get('id')


def validate_file(file_id, token):
    api_res = request('get', '/files/%d/' % file_id, token=token)

    if api_res.status_code != 200:
        click.echo('Invalid File', err=True)
        exit(1)

    return file_id
