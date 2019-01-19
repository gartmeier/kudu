"""CLI arguments definition.
"""
from argparse import OPTIONAL

from kudu.input import KuduArgumentParser

parser = KuduArgumentParser(
    prog='kudu'
)

parser.add_argument(
    'command',
    choices=['push', 'deploy', 'link', 'debug']
)

parser.add_argument(
    'path',
    nargs=OPTIONAL,
    default='.'
)

parser.add_argument(
    '--login',
    action='store_true'
)
