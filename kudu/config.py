from os.path import expanduser

import click
import yaml


def write_config(data, path='.kudu.yml'):
    with open(path, 'w+') as stream:
        yaml.safe_dump(data, stream, default_flow_style=False, allow_unicode=True)


def read_config(path='.kudu.yml'):
    try:
        with open(path, 'r+') as stream:
            config = yaml.load(stream.read())
    except IOError:
        config = {}

    return config


def merge_config(self, other):
    if isinstance(other, dict):
        for key, value in other.items():
            self[key] = value


def load_config():
    config = {}

    for path in (expanduser('~/.kudu.yml'), '.kudu.yml'):
        merge_config(config, read_config(path))

    return config


def get_config_key(param):
    key = param

    if param[:2] == '--':
        key = param[2:]

    aliases = {'file': 'file_id'}
    if key in aliases:
        key = aliases[key]

    return key


def get_config_value(*param_decls):
    config = load_config()
    value = None

    for param in param_decls:
        key = get_config_key(param)
        value = config.get(key)

        if value:
            break

    return value


def option(*param_decls, **attrs):
    def decorator(f):
        attrs['default'] = lambda: get_config_value(*param_decls)
        return click.option(*param_decls, **attrs)(f)

    return decorator
