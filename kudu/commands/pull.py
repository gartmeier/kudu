import os
import tempfile
from os import walk
from os.path import join, exists, isdir, relpath
from shutil import move, rmtree, copyfileobj
from zipfile import ZipFile

import click
import requests

from kudu.api import request as api_request
from kudu.config import ConfigOption
from kudu.types import PitcherFileType


def unpack_url(url):
    tmphandle, tmppath = tempfile.mkstemp(suffix='.zip')
    tmpfile = os.fdopen(tmphandle, 'r+b')

    res = requests.get(url, stream=True)

    copyfileobj(res.raw, tmpfile)
    tmpfile.close()

    with ZipFile(tmppath, 'r') as z:
        z.extractall()

    os.remove(tmppath)


def _move(src, dst):
    for root, dirs, files in walk(src):
        for name in files:
            arcroot = join(dst, relpath(root, src))
            if not exists(arcroot):
                os.makedirs(arcroot)
            move(join(root, name), join(arcroot, name))
    rmtree(src)


def to_dir(url, root_dir, base_dir, file_category):
    save_cwd = os.getcwd()

    os.chdir(root_dir)
    unpack_url(url)

    if exists(base_dir):
        _move(base_dir, os.curdir if file_category else 'interface')

    thumb_filename = base_dir + '.png'
    if exists(thumb_filename):
        os.rename(thumb_filename, 'thumbnail.png')

    os.chdir(save_cwd)


def to_file(download_url, path):
    res = requests.get(download_url, stream=True)
    with open(path, 'w+b') as f:
        copyfileobj(res.raw, f)


@click.command()
@click.option(
    '--file', '-f', 'pf',
    cls=ConfigOption,
    config_name='file_id',
    prompt='File ID',
    type=PitcherFileType()
)
@click.option(
    '--path', '-p',
    type=click.Path(),
    default=lambda: os.getcwd()
)
@click.pass_context
def pull(ctx, pf, path):
    download_url = api_request('get', '/files/%d/download-url/' % pf['id'], token=ctx.obj['token']).json()

    if isdir(path):
        filename_root, filename_ext = os.path.splitext(pf['filename'])

        if filename_ext == '.zip':
            to_dir(download_url, path, filename_root, pf['category'])
        else:
            to_file(download_url, join(path, pf['filename']))
    else:
        to_file(download_url, path)
