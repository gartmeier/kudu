import getpass
import os
from argparse import ArgumentParser, Namespace

from kudu.exceptions import InvalidPath


class KuduArgumentParser(ArgumentParser):
    """Adds additional logic to `argparse.ArgumentParser`.

    Handles all input (CLI args, file args, stdin), applies defaults,
    and performs extra validation.

    """
    args = None  # type: Namespace

    def parse_args(self, args=None, namespace=None, backend=None):
        self.args = super(KuduArgumentParser, self).parse_args(args, namespace)

        if not os.path.exists(self.args.path):
            raise InvalidPath()

        if self.args.login:
            backend.remove_token()

        if not backend.restore_token():
            username = raw_input("Username for %s: " % backend.url)
            password = getpass.getpass("Password for %s: " % backend.url)
            backend.authenticate(username, password)

        return self.args
