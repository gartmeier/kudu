"""This module provides the main functionality of the PITCHER Command Line Interface.

Invocation flow:

  1. Read, validate and process the input (args).
  2. Authenticate.
  3. Push.
  5. Exit.

"""
import fnmatch
import glob
import logging
import os
import sys
import time
from getpass import getpass
from shutil import copyfile

import requests
import yaml
from git import InvalidGitRepositoryError, Repo
from watchdog.observers import Observer

from kudu import ExitStatus
from kudu.cli import parser
from kudu.config import parse_deployments
from kudu.events import MirrorEventHandler
from kudu.exceptions import InvalidPath, InvalidAuth, UnknownProvider, ConfigError, ConnectionError, BranchNotPermitted
from kudu.providers.pitcher import PitcherFileProvider

CONFIG_FILE = '.kudu.yml'


def push(args, logger):
    filename = os.path.basename(os.path.abspath(args.path))

    if os.path.isdir(args.path):
        filename += '.zip'

    provider = PitcherFileProvider()
    provider.push(filename, args.path, logger=logger)


def deploy(args, logger):
    root_dir = os.path.abspath(args.path)
    base_dir = os.curdir

    while root_dir != '/' and not os.path.exists(os.path.join(root_dir, CONFIG_FILE)):
        root_dir = os.path.dirname(root_dir)
        base_dir = os.path.relpath(args.path, root_dir)

    if root_dir == '/':
        raise ConfigError('file \'%s\' not found in the current or any of the parent directories' % CONFIG_FILE)

    save_cwd = os.getcwd()
    os.chdir(root_dir)

    try:
        try:
            active_branch = str(Repo().active_branch)
        except InvalidGitRepositoryError:
            active_branch = None

        deployments = parse_deployments(CONFIG_FILE, base_dir, active_branch, logger)

        for i, deployment in enumerate(deployments):
            logging.info('Deploying %d/%d' % (i + 1, len(deployments)))
            deployment.deploy()
    finally:
        os.chdir(save_cwd)


def walk(top, **kwargs):
    for root, dirs, files in os.walk(top):
        root_relpath = os.path.relpath(root, top)

        if 'ignore' in kwargs:
            ignore = False

            for item in kwargs['ignore']:
                if fnmatch.fnmatch(root_relpath, item):
                    ignore = True
                    break

            if ignore:
                continue

        for name in files:
            file_relpath = os.path.join(root_relpath, name) if root_relpath != '.' else name
            ignore = False

            if 'ignore' in kwargs:
                for ignore_relpath in kwargs['ignore']:
                    if fnmatch.fnmatch(ignore_relpath, file_relpath):
                        ignore = True
                        break

            if not ignore:
                yield os.path.join(root, name)


def sync_dir(source, target, logger, **kwargs):
    total_files = 0
    current_file = 0

    sys.stdout.write('Count files')

    for _ in walk(source, **kwargs):
        total_files += 1
        sys.stdout.write('\rCounting files: %d' % total_files)

    sys.stdout.write('\rCounting files: %d, done.\n' % total_files)
    sys.stdout.write('Copying files')

    for src in walk(source, **kwargs):
        current_file += 1
        sys.stdout.write('\rCopying files: %d/%d' % (current_file, total_files))

        dst = os.path.join(target, os.path.relpath(src, source))

        try:
            os.makedirs(os.path.dirname(dst))
        except OSError:
            pass

        copyfile(src, dst)

        if kwargs.get('scripts') \
                and len(kwargs['scripts']) > 0 \
                and os.path.splitext(dst)[1] == '.html':
            add_scripts(dst, kwargs['scripts'])

    sys.stdout.write('\rCopying files: %d/%d, done.\n' % (current_file, total_files))

    if 'rename' in kwargs:
        sys.stdout.write('Renaming files')

        for i, rename in enumerate(kwargs['rename']):
            sys.stdout.write('\rRename files: %d/%d' % (i + 1, len(kwargs['rename'])))

            abssource = os.path.join(target, rename['source'])
            abstarget = os.path.join(target, rename['target'])

            if os.path.isdir(abstarget):
                for match in glob.glob(abssource):
                    if not os.path.isdir(os.path.join(abstarget, os.path.basename(match))):
                        os.rename(match, os.path.join(abstarget, os.path.basename(match)))
            elif os.path.exists(abssource):
                os.rename(abssource, abstarget)

        sys.stdout.write('\rRenaming files: %d/%d, done.\n' % (len(kwargs['rename']), len(kwargs['rename'])))


def add_scripts(path, scripts):
    # Read in the file
    with open(path, 'r') as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace('</body>', '<script src="' + '"></script><script src="'.join(scripts) + '"></script></body>')

    # Write the file out again
    with open(path, 'w') as file:
        file.write(filedata)


def watch_dir(source, target, logger, **kwargs):
    event_handler = MirrorEventHandler(source, target, **kwargs)
    observer = Observer()
    observer.schedule(event_handler, source, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def link_dir(source, target, logger, **kwargs):
    sync_dir(source, target, logger, **kwargs)
    watch_dir(source, target, logger, **kwargs)


def link(args, logger, vorlon_url=None):
    try:
        with open(os.path.expanduser('~/.kudu/config.yml'), 'r') as stream:
            kudu_config = yaml.load(stream)
    except IOError:
        raise ConfigError('file ~/.kudu/config.yml not found')

    if args.parallels:
        if not kudu_config.get('parallels_local_state'):
            raise ConfigError('missing argument \'parallels_local_state\' in ~/.kudu/config.yml')

        dest_root = kudu_config.get('parallels_local_state')

        if not os.path.exists(dest_root):
            raise ConfigError('invalid \'parallels_local_state\' in ~/.kudu/config.yml')

    else:
        if not kudu_config.get('simulator_pitcher_folders'):
            raise ConfigError('missing argument \'simulator_pitcher_folders\' in ~/.kudu/config.yml')

        dest_root = kudu_config.get('simulator_pitcher_folders')

        if not os.path.exists(dest_root):
            raise ConfigError('invalid\'simulator_pitcher_folders\' in ~/.kudu/config.yml')

    # parse config
    root_dir = os.path.abspath(args.path)
    base_dir = os.curdir

    while root_dir != '/' and not os.path.exists(os.path.join(root_dir, CONFIG_FILE)):
        root_dir = os.path.dirname(root_dir)
        base_dir = os.path.relpath(args.path, root_dir)

    if root_dir == '/':
        raise ConfigError('file \'%s\' not found in the current or any of the parent directories' % CONFIG_FILE)

    config = None

    with open(os.path.join(root_dir, CONFIG_FILE), 'r') as stream:
        configs = yaml.load(stream)

        if isinstance(configs, list):
            for c in configs:
                if c.get('path') == base_dir:
                    config = c
        elif isinstance(configs, dict):
            config = configs

    if not config:
        raise InvalidPath()

    # get file id
    file_id = config.get('id')

    if file_id is None:
        raise ConfigError('missing argument \'id\'')

    if isinstance(file_id, dict):
        try:
            active_branch = str(Repo(root_dir).active_branch)
        except InvalidGitRepositoryError:
            active_branch = None

        if active_branch not in file_id:
            raise BranchNotPermitted

        file_id = file_id[active_branch]

    # get filename from api
    files = PitcherFileProvider()

    if not files.restore_token():
        username = raw_input("Username for %s: " % files.api_url)
        password = getpass("Password for %s: " % files.api_url)
        files.authenticate(username, password)

    file = files.get_file(file_id)
    valid_categories = ['presentation', 'zip', '']

    if file.get('category') not in valid_categories:
        raise ConfigError('invalid category \'%s\' (\'%s\')' % (file.get('category'), '\', \''.join(valid_categories)))

    if file.get('category') == 'presentation':
        file_dir = 'slides/%s' % os.path.splitext(file.get('filename'))[0]
        dest_dir = os.path.join(dest_root, file_dir)
    elif file.get('category') == 'zip':
        file_dir = 'zip/%s' % os.path.splitext(file.get('filename'))[0]
        dest_dir = os.path.join(dest_root, file_dir)
    else:
        dest_dir = os.path.join(dest_root)

    link_dir(
        os.path.join(root_dir, base_dir), dest_dir, logger,
        rename=[
            {'source': 'thumbnail.png', 'target': os.path.splitext(file.get('filename'))[0] + '.png'},
            {'source': 'ipadOnly/*', 'target': './'},
            {'source': 'interface/*', 'target': './' + os.path.splitext(file.get('filename'))[0] + '/'}
        ],
        ignore=[
            '.idea*', '__MACOSX*', '.DS_Store*', 'windowsOnly*'
        ],
        scripts=[vorlon_url] if vorlon_url else None
    )


def debug(args, logger):
    try:
        with open(os.path.expanduser('~/.kudu/config.yml'), 'r') as stream:
            kudu_config = yaml.load(stream)
    except IOError:
        raise ConfigError('file ~/.kudu/config.yml not found')

    if not kudu_config.get('vorlon_url'):
        raise ConfigError('missing argument \'vorlon_url\' in ~/.kudu/config.yml')

    link(args, logger, vorlon_url=kudu_config.get('vorlon_url'))


def main(args=sys.argv[1:]):
    """
    Validate args and run the command with error handling.

    """
    logging.basicConfig(stream=sys.stdout, format='%(message)s', level=logging.INFO)
    logger = logging.getLogger()

    exit_status = ExitStatus.SUCCESS

    try:
        parsed_args = parser.parse_args(args=args)

        commands = {'push': push, 'deploy': deploy, 'link': link, 'debug': debug}
        commands[parsed_args.command](args=parsed_args, logger=logger)

    except KeyboardInterrupt:
        logger.error('')
        exit_status = ExitStatus.ERROR_CTRL_C

    except SystemExit:
        logger.error('')
        exit_status = ExitStatus.ERROR

    except ConfigError as e:
        logger.error(e)
        exit_status = ExitStatus.ERROR

    except requests.ConnectionError:
        logger.error('Connection failed')
        exit_status = ExitStatus.ERROR

    except ConnectionError as e:
        logger.error(e)
        exit_status = ExitStatus.ERROR

    except requests.Timeout:
        logger.error('Request timed out')
        exit_status = ExitStatus.ERROR

    except requests.TooManyRedirects:
        logger.error('Too many redirects')
        exit_status = ExitStatus.ERROR_TOO_MANY_REDIRECTS

    except InvalidPath:
        logger.error('Invalid path')
        exit_status = ExitStatus.ERROR

    except InvalidAuth as e:
        logger.error(e.message)
        exit_status = ExitStatus.ERROR

    except InvalidGitRepositoryError:
        logger.error('git: not a repository')
        exit_status = ExitStatus.ERROR

    except UnknownProvider as e:
        logger.error(e)
        exit_status = ExitStatus.ERROR

    return exit_status
