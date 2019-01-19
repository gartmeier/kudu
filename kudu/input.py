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

        return self.args
