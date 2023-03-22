import click
import requests

from kudu.api import request as api_request
from kudu.config import ConfigOption
from kudu.types import PitcherFileType
from kudu.file import get_file_data, update_file_metadata


@click.command()
@click.option(
    '--file',
    '-f',
    'pf',
    cls=ConfigOption,
    config_name='file_id',
    prompt=True,
    type=PitcherFileType(category=('zip', 'presentation', 'json', ''))
)
@click.option('--path', '-p', type=click.Path(exists=True), default=None)
@click.pass_context
def push(ctx, pf, path):
    url = '/files/%d/upload-url/' %  pf['id']
    response = api_request('get', url, token=ctx.obj['token'])

    data = get_file_data(pf['filename'], pf['category'], path)

    # upload data
    requests.put(response.json(), data=data)

    # touch file
    update_file_metadata(ctx.obj['token'],  pf['id'])