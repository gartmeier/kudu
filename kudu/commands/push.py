import os
import tempfile
import zipfile
from datetime import datetime

import click
import requests

from kudu.api import request as api_request
from kudu.config import ConfigOption
from kudu.types import PitcherFileType


def make_archive(base_name, root_dir):
    save_cwd = os.getcwd()
    os.chdir(root_dir)

    th, tp = tempfile.mkstemp('.zip')
    zf = zipfile.ZipFile(tp, 'w', zipfile.ZIP_DEFLATED)

    for root, dirs, files in os.walk(os.getcwd()):
        arcroot = os.path.relpath(root)
        for name in files:
            arcname = name if not (arcroot == os.curdir and name == 'thumbnail.png') else base_name + '.png'
            zf.write(os.path.join(root, name), os.path.join(base_name, arcroot, arcname))

    zf.close()
    os.chdir(save_cwd)

    return th, tp


@click.command()
@click.option(
    '--file', '-f', 'pf',
    cls=ConfigOption,
    config_name='file_id',
    prompt=True,
    type=PitcherFileType(
        category=('zip', 'presentation', 'json')
    )
)
@click.option(
    '--path', '-p',
    default=lambda: os.getcwd()
)
@click.pass_context
def push(ctx, pf, path):
    root, ext = os.path.splitext(pf['filename'])
    upload_url = api_request('get', '/files/%d/upload-url/' % pf['id'], token=ctx.obj['token']).json()

    if os.path.isdir(path):
        th, tp = make_archive(root, path)
        requests.put(upload_url, data=os.fdopen(th, 'r+b'))
        os.remove(tp)
    else:
        requests.put(upload_url, data=open(path, 'r+b'))

    api_request(
        'patch',
        '/files/%d/' % pf['id'],
        json={'creationTime': datetime.utcnow().isoformat()},
        token=ctx.obj['token']
    )
