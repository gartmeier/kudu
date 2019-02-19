import zipfile
from os import remove, listdir
from os.path import splitext, join, exists, isdir
from shutil import copyfileobj, move

import click
import requests

from kudu.api import request as api_request
from kudu.types import PitcherFileType


@click.command()
@click.option('--file', '-f', 'pfile', prompt='File ID', type=PitcherFileType())
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
