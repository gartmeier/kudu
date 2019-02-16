import os
from shutil import copyfile

import click
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_MODIFIED, EVENT_TYPE_MOVED, EVENT_TYPE_CREATED


class CopyFilesEventHandler(FileSystemEventHandler):

    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

    def on_any_event(self, event):
        if event.event_type in [EVENT_TYPE_MODIFIED, EVENT_TYPE_MOVED, EVENT_TYPE_CREATED] and not event.is_directory:
            src_path = event.src_path if event.event_type != EVENT_TYPE_MOVED else event.dest_path
            relpath = os.path.relpath(src_path)
            click.echo("Copying file: %s" % relpath, nl=False)
            copyfile(src_path, os.path.join(self.dst, relpath))
            click.echo("\rCopying file: %s, done." % relpath)
