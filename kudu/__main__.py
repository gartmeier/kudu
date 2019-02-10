#!/usr/bin/env python
from os.path import expanduser

import anyconfig
import click

from kudu.api import authenticate
from kudu.commands.deploy import deploy
from kudu.commands.init import init
from kudu.commands.link import link
from kudu.commands.pull import pull
from kudu.commands.push import push


@click.group()
@click.option('--username', prompt=True, envvar='KUDU_USERNAME')
@click.option('--password', prompt=True, envvar='KUDU_PASSWORD')
@click.option('--token', envvar='KUDU_TOKEN')
@click.pass_context
def cli(ctx, username, password, token):
    if not token:
        try:
            token = authenticate(username, password)
        except ValueError:
            click.echo('Invalid username or password', err=True)
            exit(1)

    ctx.obj = {
        'username': username,
        'password': password,
        'token': token
    }


cli.add_command(init)
cli.add_command(push)
cli.add_command(pull)
cli.add_command(deploy)
cli.add_command(link)

if __name__ == '__main__':
    cli(default_map=anyconfig.load([expanduser('~/.kudu.yml'), '.kudu.yml']))
