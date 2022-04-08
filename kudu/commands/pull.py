import os
import shutil
import tempfile
from os import walk
from os.path import exists, isdir, join, relpath
from shutil import copyfileobj, move, rmtree
from zipfile import ZipFile

import click
import requests

from kudu.api import api
from kudu.config import ConfigOption
from kudu.types import PitcherFileType


def unpack_url(url):
    tmphandle, tmppath = tempfile.mkstemp(suffix=".zip")
    tmpfile = os.fdopen(tmphandle, "r+b")

    res = requests.get(url, stream=True)

    copyfileobj(res.raw, tmpfile)
    tmpfile.close()

    with ZipFile(tmppath, "r") as z:
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
        _move(base_dir, os.curdir if file_category else "interface")

    thumb_filename = base_dir + ".png"
    if exists(thumb_filename):
        os.rename(thumb_filename, "thumbnail.png")

    os.chdir(save_cwd)


def to_file(download_url, path):
    res = requests.get(download_url, stream=True)
    with open(path, "w+b") as f:
        copyfileobj(res.raw, f)


@click.command()
@click.option(
    "--file",
    "-f",
    cls=ConfigOption,
    config_name="file_id",
    prompt="File ID",
    type=PitcherFileType(),
)
@click.option(
    "--path",
    "-p",
    type=click.Path(),
    default=os.curdir,
)
@click.pass_context
def pull(file, path):
    url = api.get_download_url()
    filename = get_filename(file, path)
    download_file(url, filename)

    root, ext = os.path.splitext(filename)
    if ext == ".zip":
        extract_dir = os.path.dirname(root)
        shutil.unpack_archive(filename, extract_dir)


def get_filename(file, path):
    root, ext = os.path.splitext(file["filename"])

    if ext == ".zip" and os.path.isdir(path):
        return "%s.zip" % path

    if os.path.isdir(path):
        return os.path.join(path, file["filename"])

    return path


def download_file(url, filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
