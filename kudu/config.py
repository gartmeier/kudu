import os

import yaml

from kudu.exceptions import BranchNotPermitted, PathNotPermitted, ConfigError
from kudu.providers.pitcher import PitcherFileDeploymet, SftpDeployment


def parse_deployments(config_file, base_dir, active_branch, logger):
    with open(config_file, 'r') as stream:
        configs = yaml.load(stream)
        deployments = []

        if isinstance(configs, dict):
            configs = [configs]

        for config in configs:
            try:

                provider_name = config.pop('provider', 'pitcherfile')
                deployment = None

                if provider_name == 'pitcherfile':
                    deployment = parse_pitcherfile_deployment(config, base_dir, active_branch, logger)
                elif provider_name == 'pitcherforms':
                    deployment = parse_pitcherforms_deployment(config, base_dir, active_branch, logger)

                if not deployment:
                    raise ConfigError('unknown provider \'%s\'' % provider_name)

                deployments.append(deployment)

            except BranchNotPermitted:
                logger.info('Skipping deployment because this branch is not permitted: %s' % active_branch)
            except PathNotPermitted:
                logger.info('Skipping deployment because this path is not permitted: %s' % base_dir)

        return deployments


def parse_pitcherfile_deployment(config, base_dir, active_branch, logger):
    file_id = config.get('id')
    file_path = config.get('path', os.curdir)

    if file_id is None:
        raise ConfigError('missing argument \'id\'')

    if isinstance(file_id, dict):
        if active_branch not in file_id:
            raise BranchNotPermitted
        file_id = file_id[active_branch]

    if not os.path.exists(file_path):
        raise ConfigError('invalid path \'%s\'' % file_path)

    if base_dir != os.curdir and base_dir != file_path:
        raise PathNotPermitted

    return PitcherFileDeploymet(
        file_id=file_id,
        path=file_path,
        body=config.get('body'),
        keywords=config.get('keywords'),
        logger=logger)


def parse_pitcherforms_deployment(config, base_dir, active_branch, logger):
    config_path = config.get('path', '.')

    if not os.path.exists(config_path):
        raise ConfigError('invalid path \'%s\'' % config_path)

    if base_dir != os.curdir and base_dir != config_path:
        raise PathNotPermitted

    config_files = config.get('files')

    deployment_files = []

    if config_files:
        if not isinstance(config_files, list) or len(config_files) == 0:
            raise ConfigError('provider \'pitcherforms\' requires a minimum of one file')

        for file in config_files:
            try:
                if isinstance(file, str):
                    file = {'local_path': file, 'remote_path': file}

                if 'local_path' not in file:
                    raise ConfigError('file attribute \'local_path\' required')

                if 'remote_path' not in file:
                    raise ConfigError('file attribute \'remote_path\' required')

                if isinstance(file['remote_path'], dict):
                    if active_branch not in file['remote_path']:
                        raise BranchNotPermitted()
                    file['remote_path'] = file['remote_path'][active_branch]

                file['local_path'] = os.path.join(config_path, file['local_path'])

                if not os.path.exists(file['local_path']):
                    raise ConfigError('invalid path \'%s\'' % file['local_path'])

                file['remote_path'] = os.path.join('/var/www/html/forms/sfdc/', file['remote_path'])

                deployment_files.append(file)
            except BranchNotPermitted:
                logger.info('Skipping deployment because this branch is not permitted: %s' % active_branch)

    deployment = SftpDeployment(
        'forms.pitcher.com', 'ec2-user',
        files=deployment_files, logger=logger)

    return deployment
