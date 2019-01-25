import logging
import os
from shutil import copyfile

from watchdog.events import FileSystemEventHandler


def add_scripts(path, scripts):
    # Read in the file
    with open(path, 'r') as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace('</body>', '<script src="' + '"></script><script src="'.join(scripts) + '"></script></body>')

    # Write the file out again
    with open(path, 'w') as file:
        file.write(filedata)


class MirrorEventHandler(FileSystemEventHandler):
    """Mirros all the events captured."""

    def __init__(self, src_dir=None, dest_dir=None, **kwargs):
        self.src_dir = src_dir
        self.dest_dir = dest_dir
        self.scripts = kwargs.get('scripts')

    def on_moved(self, event):
        super(MirrorEventHandler, self).on_moved(event)

        if not event.is_directory:
            src_relpath = os.path.relpath(event.src_path, self.src_dir)
            src_path = os.path.join(self.dest_dir, src_relpath)

            dest_relpath = os.path.relpath(event.dest_path, self.src_dir)
            dest_path = os.path.join(self.dest_dir, dest_relpath)
            dest_dirname = os.path.dirname(dest_path)

            if not os.path.exists(dest_dirname):
                os.makedirs(dest_dirname)

            os.rename(src_path, dest_path)

            if self.scripts and len(self.scripts) > 0 \
                    and os.path.splitext(dest_path)[1] == '.html':
                add_scripts(dest_path, self.scripts)

            logging.info("Moved file: from %s to %s", src_relpath, dest_relpath)

    def on_created(self, event):
        super(MirrorEventHandler, self).on_created(event)

        if not event.is_directory:
            dest_relpath = os.path.relpath(event.src_path, self.src_dir)
            dest_path = os.path.join(self.dest_dir, dest_relpath)
            dest_dirname = os.path.dirname(dest_path)

            if not os.path.exists(dest_dirname):
                os.makedirs(dest_dirname)

            copyfile(event.src_path, dest_path)

            if self.scripts and len(self.scripts) > 0 \
                    and os.path.splitext(dest_path)[1] == '.html':
                add_scripts(dest_path, self.scripts)

            logging.info("Created file: %s", dest_relpath)

    def on_deleted(self, event):
        super(MirrorEventHandler, self).on_deleted(event)

        if not event.is_directory:
            dest_relpath = os.path.relpath(event.src_path, self.src_dir)
            dest_path = os.path.join(self.dest_dir, dest_relpath)

            os.remove(dest_path)

            logging.info("Deleted file: %s", dest_relpath)

    def on_modified(self, event):
        super(MirrorEventHandler, self).on_modified(event)

        if not event.is_directory:
            dest_relpath = os.path.relpath(event.src_path, self.src_dir)
            dest_path = os.path.join(self.dest_dir, dest_relpath)
            dest_dirname = os.path.dirname(dest_path)

            if not os.path.exists(dest_dirname):
                os.makedirs(dest_dirname)

            copyfile(event.src_path, dest_path)

            if self.scripts and len(self.scripts) > 0 \
                    and os.path.splitext(dest_path)[1] == '.html':
                add_scripts(dest_path, self.scripts)

            logging.info("Modified file: %s", dest_relpath)
