import os
import shutil
import tempfile
import zipfile
from os.path import basename, splitext, join, exists, dirname
from urlparse import urlparse

import click
import requests

from kudu.api import authenticate
from kudu.api import request as api_request
from kudu.config import read_config, read_global_config


@click.command()
@click.option('--path', default=os.getcwd(), type=click.Path(exists=True))
def pull(path):
    global_config = None

    try:
        global_config = read_global_config()
    except IOError:
        click.echo('Run "kudu init" first', True)
        exit(1)

    token = None

    try:
        token = authenticate(global_config.get('username'), global_config.get('password'))
    except ValueError:
        click.echo('Invalid username or password', err=True)
        exit(1)

    config = None

    try:
        config = read_config(path)
    except IOError:
        click.echo('Not a kudu repository', True)
        exit(1)

    res = api_request('get', '/files/%d/download-url/' % config.get('id'), token=token)
    url = res.json()

    if res.status_code != 200:
        if res.status_code == 404:
            click.echo('Invalid file', err=True)
        else:
            click.echo('Unknown error', err=True)
        exit(1)

    url_path = urlparse(url).path
    url_basename = basename(url_path)
    url_filename, url_ext = splitext(url_basename)
    zip_file = os.path.join(tempfile.gettempdir(), url_basename)

    with open(zip_file, 'w+') as stream:
        r = requests.get(url, stream=True)
        shutil.copyfileobj(r.raw, stream)

    try:
        with zipfile.ZipFile(zip_file) as stream:
            for member in stream.namelist():
                target_basename = basename(member)

                if not target_basename:
                    continue

                if target_basename == url_filename + '.png':
                    target_basename = 'thumbnail.png'

                target_dirname = join(path, '/'.join(dirname(member).split('/')[1:]))

                if not exists(target_dirname):
                    os.makedirs(target_dirname)

                source_stream = stream.open(member)
                target_path = join(target_dirname, target_basename)
                target_stream = file(target_path, "wb")

                with source_stream, target_stream:
                    shutil.copyfileobj(source_stream, target_stream)
    except zipfile.BadZipfile:
        click.echo('File is not a zip file', err=True)
        exit(1)
