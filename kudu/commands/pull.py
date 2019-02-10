import zipfile
from os import remove, listdir
from os.path import splitext, join, exists, isdir
from shutil import copyfileobj, move

import click
import requests

from kudu.api import request as api_request


class PitcherFile(click.ParamType):
    name = 'pitcher-file'

    def convert(self, value, param, ctx):
        if not isinstance(value, int) and not value.isdigit():
            self.fail('%d is not a valid integer' % value, param, ctx)

        res = api_request('get', '/files/%d/' % value, token=ctx.obj['token'])
        if res.status_code != 200:
            self.fail('%d is not a valid file' % value)

        return res.json()


@click.command()
@click.option('--file', '-f', 'pfile', type=PitcherFile())
@click.pass_context
def pull(ctx, pfile):
    download_url = api_request('get', '/files/%d/download-url/' % pfile['id'], token=ctx.obj['token']).json()

    with open(pfile['filename'], 'w') as stream:
        r = requests.get(download_url, stream=True)
        copyfileobj(r.raw, stream)

    root, ext = splitext(pfile['filename'])
    if ext == '.zip':
        with zipfile.ZipFile(pfile['filename'], 'r') as stream:
            stream.extractall()
        remove(pfile['filename'])

        if exists('.kudu.yml') and isdir(root):
            for filename in listdir(root):
                move(join(root, filename), filename)

            thumbnail = root + '.png'
            if exists(thumbnail):
                move(thumbnail, 'thumbnail.png')
