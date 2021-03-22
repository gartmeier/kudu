import os
import re
import tempfile
import zipfile


class NameRule:

    def __init__(self, pattern, path):
        if not isinstance(pattern, str):
            pattern = os.path.join(*pattern)
        self.pattern = re.compile(pattern)

        if not isinstance(path, str):
            path = os.path.join(*path)
        self.path = path


def mkztemp(base_name, root_dir=None, base_dir=None, name_rules=None):
    save_cwd = os.getcwd()

    if root_dir is not None:
        os.chdir(root_dir)

    if base_dir is None:
        base_dir = os.curdir

    try:
        tmp_fd, tmp_name = tempfile.mkstemp('.zip')
        zf = zipfile.ZipFile(tmp_name, 'w', zipfile.ZIP_DEFLATED)

        for root, dirs, files in os.walk(base_dir):
            arcroot = os.path.relpath(root)

            for name in files:
                if arcroot == os.curdir:
                    arcname = name
                else:
                    arcname = os.path.join(arcroot, name)

                if name_rules:
                    for rule in name_rules:
                        m = rule.pattern.match(arcname)
                        if m:
                            arcname = rule.path.format(
                                *m.groups(), base_name=base_name
                            )

                filename = os.path.join(root, name)
                zf.write(filename, arcname)
    finally:
        if root_dir is not None:
            os.chdir(save_cwd)

    return tmp_fd, tmp_name
