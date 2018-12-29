import sys


def log(message):
    sys.stdout.write('{}\n'.format(message))


def error(message):
    sys.stderr.write('{}\n'.format(message))
