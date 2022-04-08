from click.types import IntParamType
from requests import HTTPError

from kudu.api import api


class PitcherFileType(IntParamType):
    name = 'pitcher-file'

    def __init__(self, category=None):
        self.category = category

    def convert(self, value, param, ctx):
        value = super(PitcherFileType, self).convert(value, param, ctx)

        try:
            return api.get_file(value)
        except HTTPError as e:
            print(e)
            self.fail('%d is not a valid file' % value)
