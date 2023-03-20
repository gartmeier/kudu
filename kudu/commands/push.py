import os
import time
import click
import requests

from kudu.api import request as api_request
from kudu.config import ConfigOption
from kudu.types import PitcherFileType
from kudu.file import get_file_data, update_file_metadata, upload_file


@click.command()
@click.option(
    '--file',
    '-f',
    'pf',
    cls=ConfigOption,
    config_name='file_id',
    required=False,
    type=PitcherFileType(category=('zip', 'presentation', 'json', ''))
)
@click.option('--path', '-p', type=click.Path(exists=True), default=None)
@click.option('--instance', '-i', type=int, required=False, help="instance id to upload file")
@click.option('--body', '-b', type=str, required=False, help="Body of the file")
@click.option('--filename', '-n', type=str, required=False, help="Name of the file in bucket")
@click.option('--extension', '-e', type=str, required=False, default="zip", help="Extension of the file that's going to be uploaded, default 'zip'")
@click.pass_context
def push(ctx, pf, path, instance, body, filename, extension):
    if pf:
        create_or_update_file(ctx.obj['token'], filename=pf['filename'], path=path, file_id=pf['id'], category=pf['category'])
    else:
        if not instance or not body:
            click.echo('instance and body should be provided when creating a new file', err=True)
            exit(1)
        create_or_update_file(ctx.obj['token'], filename=filename, path=path, body=body, instance=instance, category=extension)

def create_or_update_file(token, filename, path = None, file_id=None, body=None, instance=None, category = None):
    file_data = get_file_data(filename=filename, category=category, path=path)
    file_id = upload_file(token, instance, body, file_data=file_data, file_name=filename, file_id=file_id)
    update_file_metadata(token, file_id)
