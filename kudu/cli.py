import click

from kudu.commands.deploy import deploy
from kudu.commands.init import init
from kudu.commands.link import link
from kudu.commands.pull import pull
from kudu.commands.push import push


@click.group()
def cli():
    pass


cli.add_command(init)
cli.add_command(push)
cli.add_command(pull)
cli.add_command(deploy)
cli.add_command(link)
