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
from kudu.config import InvalidConfig
from kudu.exceptions import FileNotFound, ConfigNotFound, InvalidPath, InvalidAuth

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
    deployment_path = None

    while proj_dir != '/' and not os.path.exists(os.path.join(proj_dir, CONFIG)):
        proj_dir = os.path.dirname(proj_dir)
        deployment_path = os.path.relpath(args.path, proj_dir)

    if proj_dir == '/':
        raise ConfigNotFound()

    save_cwd = os.getcwd()
    os.chdir(proj_dir)

    try:
        with open(os.path.join(proj_dir, CONFIG), 'r') as stream:
            deployments = yaml.load(stream)

            if isinstance(deployments, dict):
                deployments = [deployments]

            for deployment in deployments:
                if isinstance(deployment['id'], dict):
                    active_branch = str(Repo(proj_dir).active_branch)

                    if active_branch not in deployment['id']:
                        logger.log('Skipping a deployment because this branch is not permitted: %s' % active_branch)
                        continue

                    deployment['id'] = deployment['id'][active_branch]

                if 'path' not in deployment:
                    deployment['path'] = proj_dir

                if deployment_path and deployment_path != deployment['path']:
                    continue

                if 'thumbnail' not in deployment:
                    deployment['thumbnail'] = 'thumbnail.png'

                file_data = files.get_file(backend, deployment['id'])
                file_upload = deployment['path']

                if os.path.isdir(deployment['path']):
                    target_basename = file_data['filename']
                    target_filename = os.path.splitext(target_basename)[0]
                    target_path = os.path.join('..', target_filename)
                    target_thumb = target_filename + '.png'

                    if os.path.exists(deployment['thumbnail']):
                        os.rename(deployment['thumbnail'], target_thumb)

                    try:
                        logger.log('Create %s' % target_basename)

                        file_upload = os.path.join(tempfile.tempdir, target_filename)

                        os.rename(deployment['path'], target_path)
                        shutil.make_archive(file_upload, 'zip', '..', target_filename)

                        file_upload += '.zip'
                    finally:
                        os.rename(target_path, deployment['path'])

                        if os.path.exists(target_thumb):
                            os.rename(target_thumb, deployment['thumbnail'])

                logger.log('Upload file %s' % file_data['id'])

                files.upload_file(backend, file_data['id'], file_upload)

                files.save_file(
                    backend, file_data['id'],
                    body=deployment.get('body'),
                    keywords=deployment.get('keywords'),
                    creation_time=datetime.utcnow().isoformat()
                )

                if os.path.isdir(deployment['path']):
                    os.remove(file_upload)
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

    except InvalidConfig as e:
        logger.error('config: %s.' % e.message)
        exit_status = ExitStatus.ERROR

    except InvalidGitRepositoryError:
        logger.error('git: not a repository')
        exit_status = ExitStatus.ERROR

    return exit_status
