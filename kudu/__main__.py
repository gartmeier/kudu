#!/usr/bin/env python

import click

from kudu.api import authenticate
from kudu.commands.create import create
from kudu.commands.init import init
from kudu.commands.link import link
from kudu.commands.pull import pull
from kudu.commands.push import push
from kudu.config import default_password, default_token, default_username


@click.group()
@click.option(
    "--username",
    "-u",
    prompt=True,
    envvar="KUDU_USERNAME",
    default=default_username,
)
@click.option(
    "--password",
    "-p",
    prompt=True,
    hide_input=True,
    envvar="KUDU_PASSWORD",
    default=default_password,
)
@click.option("--token", "-t", envvar="KUDU_TOKEN", default=default_token)
@click.pass_context
def cli(ctx, username, password, token):
    if not token:
        try:
            token = authenticate(username, password)
        except ValueError:
            click.echo("Invalid username or password", err=True)
            exit(1)

    ctx.obj = {"username": username, "password": password, "token": token}


cli.add_command(init)
cli.add_command(pull)
cli.add_command(push)
cli.add_command(link)
cli.add_command(create)

if __name__ == "__main__":
    cli()
