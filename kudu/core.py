"""This module provides the main functionality of the PITCHER Command Line Interface.

Invocation flow:

  1. Read, validate and process the input (args).
  2. Authenticate.
  3. Push.
  5. Exit.

"""
import logging
import os
import sys

import requests
from git import InvalidGitRepositoryError, Repo

from kudu import ExitStatus
from kudu.cli import parser
from kudu.config import parse_deployments
from kudu.exceptions import InvalidPath, InvalidAuth, UnknownProvider, ConfigError, ConnectionError
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


def main(args=sys.argv[1:]):
    """
    Validate args and run the command with error handling.

    """
    logging.basicConfig(stream=sys.stdout, format='%(message)s', level=logging.INFO)
    logger = logging.getLogger()

    exit_status = ExitStatus.SUCCESS

    try:
        parsed_args = parser.parse_args(args=args)

        commands = {'push': push, 'deploy': deploy}
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
