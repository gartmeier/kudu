"""This module provides the main functionality of the PITCHER Command Line Interface.

Invocation flow:

  1. Read, validate and process the input (args).
  2. Authenticate.
  3. Push.
  5. Exit.

"""
import os
import shutil
import sys
import tempfile
from datetime import datetime

import requests
import yaml
from git import InvalidGitRepositoryError, Repo

from kudu import ExitStatus, logger, files
from kudu.backend import Backend
from kudu.cli import parser
from kudu.exceptions import FileNotFound, ConfigNotFound, InvalidPath, InvalidAuth, BranchNotPermitted

CONFIG = '.kudu.yml'


def push(args, backend):
    filename = os.path.basename(args.path)

    if os.path.isdir(args.path):
        filename += '.zip'

    res = files.get_files(backend, filename=filename)

    if len(res) == 0:
        raise FileNotFound('invalid filename \'{filename}\''.format(filename=filename))

    for file_data in res:
        upload_path = args.path

        if os.path.isdir(args.path):
            root_dir = os.path.dirname(args.path)
            base_dir = os.path.basename(args.path)
            zip_dir = os.path.join(tempfile.tempdir, base_dir)

            logger.log('Create archive: %s' % filename)
            shutil.make_archive(zip_dir, 'zip', root_dir, base_dir)

            upload_path = zip_dir + '.zip'

        logger.log('Upload to file: %s' % file_data['id'])

        files.upload_file(backend, file_data['id'], upload_path)
        files.save_file(backend, file_data['id'], creation_time=datetime.utcnow().isoformat())

        if os.path.isdir(args.path):
            os.remove(upload_path)


def deploy(args, backend):
    proj_dir = os.path.abspath(args.path)
    target_path = None

    while proj_dir != '/' and not os.path.exists(os.path.join(proj_dir, CONFIG)):
        proj_dir = os.path.dirname(proj_dir)
        target_path = os.path.relpath(args.path, proj_dir)

    if proj_dir == '/':
        raise ConfigNotFound()

    try:
        active_branch = str(Repo(proj_dir).active_branch)
    except InvalidGitRepositoryError:
        active_branch = None

    save_cwd = os.getcwd()
    os.chdir(proj_dir)

    try:
        with open(os.path.join(proj_dir, CONFIG), 'r') as stream:
            deployments = yaml.load(stream)

            if isinstance(deployments, dict):
                deployments = [deployments]

            for deployment in deployments:

                # apply defaults
                if 'path' not in deployment:
                    deployment['path'] = '.'

                # filter
                if target_path and target_path != deployment['path']:
                    continue

                try:
                    files.deploy_file(backend, deployment, active_branch)
                except BranchNotPermitted as e:
                    logger.log(e.message)
    finally:
        os.chdir(save_cwd)


def main(args=sys.argv[1:]):
    """
    Validate args and run the command with error handling.

    """

    exit_status = ExitStatus.SUCCESS

    try:
        backend = Backend()
        parsed_args = parser.parse_args(args=args, backend=backend)

        commands = {'push': push, 'deploy': deploy}
        commands[parsed_args.command](args=parsed_args, backend=backend)

    except KeyboardInterrupt:
        logger.error('')
        exit_status = ExitStatus.ERROR_CTRL_C

    except SystemExit:
        logger.error('')
        exit_status = ExitStatus.ERROR

    except requests.ConnectionError:
        logger.error('Connection failed')
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

    except ConfigNotFound:
        logger.error('fatal: no %s found in the current or any of the parent directories' % CONFIG)
        exit_status = ExitStatus.ERROR

    except InvalidGitRepositoryError:
        logger.error('git: not a repository')
        exit_status = ExitStatus.ERROR

    return exit_status
