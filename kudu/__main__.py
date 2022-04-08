#!/usr/bin/env python

import click
from requests import HTTPError

from kudu.api import api
from kudu.commands.pull import pull
from kudu.commands.push import push
from kudu.config import ConfigOption


@click.group()
@click.option(
    "--username",
    "-u",
    cls=ConfigOption,
    prompt=True,
    envvar="KUDU_USERNAME",
)
@click.option(
    "--password",
    "-p",
    cls=ConfigOption,
    prompt=True,
    hide_input=True,
    envvar="KUDU_PASSWORD",
)
@click.option(
    "--token",
    "-t",
    cls=ConfigOption,
    envvar="KUDU_TOKEN",
)
def cli(username, password, token):
    try:
        api.set_token(token) if token else api.authenticate(username, password)
    except HTTPError:
        click.echo("Invalid username or password", err=True)
        exit(1)


cli.add_command(pull)
cli.add_command(push)

if __name__ == "__main__":
    cli()
