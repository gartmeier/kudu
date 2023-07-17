from os.path import expanduser

import yaml


def write_config(data, path=".kudu.yml"):
    with open(path, "w+") as stream:
        yaml.safe_dump(data, stream, default_flow_style=False, allow_unicode=True)


def read_config(path=".kudu.yml"):
    try:
        with open(path, "r+") as stream:
            try:
                from yaml import CDumper as Dumper
                from yaml import CLoader as Loader
            except ImportError:
                from yaml import Loader

            config = yaml.load(stream.read(), Loader=Loader)
    except IOError:
        config = {}

    return config


def merge_config(self, other):
    if isinstance(other, dict):
        for key, value in other.items():
            self[key] = value


def load_config():
    config = {}

    for path in (expanduser("~/.kudu.yml"), ".kudu.yml"):
        merge_config(config, read_config(path))

    return config


def default_username():
    return load_config().get("username")


def default_password():
    return load_config().get("password")


def default_token():
    return load_config().get("token")


def default_file_id():
    return load_config().get("file_id")


def default_pitcher_folders():
    return load_config().get("pitcher_folders")
