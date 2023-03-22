import click

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


def create_file(token, app_id, file_body, download_url = None):
    requestJSON = {
        'app':
            app_id,
        'body':
            file_body
    }

    if download_url:
        requestJSON['downloadUrl'] = download_url

    res = request(
        'post',
        '/files/',
        json=requestJSON,
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
        click.echo('Invalid file', err=True)
        exit(1)

    if api_res.json().get('category') not in ('zip', 'presentation', ''):
        click.echo('Invalid category', err=True)
        exit(1)

    return file_id
