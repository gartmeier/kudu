from os.path import expanduser, join

import yaml


def read_config(path):
    with open(path, 'r+') as stream:
        return yaml.load(stream.read())


def read_global_config():
    return read_config(path=expanduser('~/.kudu.yml'))


def write_config(data, path='.kudu.yml'):
    with open(path, 'w+') as stream:
        yaml.safe_dump(data, stream, default_flow_style=False, allow_unicode=True)


def write_global_config(data):
    write_config(data, path=expanduser('~/.kudu.yml'))
