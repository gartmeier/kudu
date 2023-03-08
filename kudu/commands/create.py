import click
import os

from kudu.config import write_config
from kudu.commands.init import create_file
from kudu.commands.push import upload_file
from kudu.api import request as api_request

@click.command()
@click.option('--appid', '-a', type=int, required=True, help="appId")
@click.option('--body', '-b', type=str, required=True, help="Body of the file")
@click.pass_context
def create(ctx, appid, body):
    token = ctx.obj['token']
    file_id = create_file(token, appid, body)
    write_config({'file_id': file_id})
    pitcher_file = get_pitcher_file(file_id, token)
    upload_file(token, pitcher_file)

def get_pitcher_file(file_id, token):
    res = api_request('get', '/files/%d/' % file_id, token=token)
    if res.status_code != 200:
        raise Exception('%d is not a valid file' % file_id)

    return res.json()