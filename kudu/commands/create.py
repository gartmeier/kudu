import click
import time

from kudu.api import request as api_request
from kudu.file import create_file, update_file_metadata, get_file_data

@click.command()
@click.option('--instance', '-i', type=int, required=True, help="instance id to upload file")
@click.option('--body', '-b', type=str, required=True, help="Body of the file")
@click.option('--filename', '-f', type=str, required=False, help="Name of the file in bucket")
@click.pass_context
def create(ctx, instance, body, filename = None):
    if not filename:
        filename = str(time.time() * 1000)

    file_data = get_file_data(filename=filename, category='zip')
    file_id = create_file(ctx.obj['token'], instance, body, file_data=file_data)
    update_file_metadata(ctx.obj['token'], file_id)


def get_pitcher_file(file_id, token):
    res = api_request('get', '/files/%d/' % file_id, token=token)
    if res.status_code != 200:
        raise Exception('%d is not a valid file' % file_id)

    return res.json()