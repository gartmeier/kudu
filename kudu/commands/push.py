import os
from zipfile import ZipFile

import click
import requests

from kudu.api import api
from kudu.config import ConfigOption
from kudu.types import PitcherFileType


@click.command()
@click.option(
    "--file",
    "-f",
    cls=ConfigOption,
    config_name="file_id",
    prompt=True,
    type=PitcherFileType(category=("zip", "presentation", "json", "")),
)
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True),
    default=os.curdir,
)
def push(file, path):
    if os.path.isdir(path):
        arcroot = get_arcroot(file, path)
        path = create_zip(path, arcroot)

    url = api.get_upload_url(file["id"])
    with open(path, "r+b") as f:
        requests.put(url, f)

    api.touch_file(file["id"])

def get_arcroot(file, path):
    root, ext = os.path.splitext(file["filename"])

    if file["category"] == "" and has_base_interface(path):
        return os.curdir
    
    return root


def has_base_interface(path):
    path = os.path.join(path, "interface_1")
    return os.path.isdir(path)


def create_zip(abspath, arcroot):
    abspath = os.path.abspath(abspath)

    save_cwd = os.getcwd()
    os.chdir(abspath)

    try:
        zip_path = "%s.zip" % abspath

        if os.path.exists(zip_path):
            os.unlink(zip_path)

        with ZipFile(zip_path, 'w') as f:
            for root, dirs, files in os.walk(os.curdir):
                for name in files:
                    filename = os.path.join(root, name)
                    arcname = os.path.join(arcroot, filename)

                    if root == os.curdir and name == "thumbnail.png":
                        arcname = os.path.join(arcroot, "%s.png" % arcroot)

                    f.write(filename, arcname)
    finally:
        os.chdir(save_cwd)

    return zip_path
