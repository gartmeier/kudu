import os
import time
from shutil import copyfile

import click
from watchdog.observers import Observer

from kudu.defaults import default_pitcher_folders
from kudu.events import CopyFilesEventHandler
from kudu.types import PitcherFileType


def countfiles(top):
    click.echo('Counting files', nl=False)

    count = 0
    for root, dirs, files in os.walk(top):
        count += len(files)
        click.echo('\rCounting files: %d' % count, nl=False)

    click.echo('\rCounting files: %d, done.' % count)
    return count


def copyfiles(src, dst):
    total = countfiles(src)
    curr = 0

    if not os.path.exists(dst):
        os.makedirs(dst, 0755)

    click.echo('Copying files', nl=False)

    for root, dirs, files in os.walk(src):
        arcroot = os.path.relpath(root)
        for name in dirs:
            dirpath = os.path.join(dst, arcroot, name)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath, 0755)
        for name in files:
            curr += 1
            click.echo('\rCopying files: %d/%d' % (curr, total), nl=False)
            copyfile(os.path.join(root, name), os.path.join(dst, arcroot, name))

    click.echo('\rCopying files: %d/%d, done.' % (curr, total))


def watchfiles(src, dst):
    event_handler = CopyFilesEventHandler(src, dst)
    observer = Observer()
    observer.schedule(event_handler, src, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@click.command()
@click.option('--file', '-f', 'pitcher_file', prompt=True, type=PitcherFileType(category=['zip', 'presentation']))
@click.option('--pitcher-folders', '-p', prompt=True, default=lambda: default_pitcher_folders(),
              type=click.Path(exists=True, file_okay=False, writable=True))
def link(pitcher_file, pitcher_folders):
    src = os.getcwd()

    cat_dirname = pitcher_file.get('category') if pitcher_file.get('category') != 'presentation' else 'slides'
    file_dirname = os.path.splitext(pitcher_file.get('filename'))[0]
    dst = os.path.join(pitcher_folders, cat_dirname, file_dirname)

    copyfiles(src, dst)
    watchfiles(src, dst)
