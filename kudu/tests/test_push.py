import os
import time
import zipfile
from os import mkdir
from os.path import exists, join

from click.testing import CliRunner

from kudu.__main__ import cli
from kudu.api import authenticate
from kudu.api import request as api_request
from kudu.commands.push import CATEGORY_RULES
from kudu.config import write_config
from kudu.mkztemp import NameRule, mkztemp


def test_interface():
    runner = CliRunner()
    with runner.isolated_filesystem():
        write_config({'file_id': 1105408})

        mkdir('interface')

        with open('interface/index.html', 'a') as f:
            f.write('<html></html>')

        result = runner.invoke(cli, ['push'])
        assert result.exit_code == 0


def test_rules():
    runner = CliRunner()

    with runner.isolated_filesystem():
        mkdir('interface')
        open('interface/index.html', 'a').close()

        rules = (r.rule for r in CATEGORY_RULES if r.category == '')
        _, name = mkztemp('interface_test', name_rules=rules)

        zf = zipfile.ZipFile(name)
        assert zf.namelist() == ['interface_test/index.html']

    with runner.isolated_filesystem():
        open('index.html', 'a').close()
        open('thumbnail.png', 'a').close()

        rules = [r.rule for r in CATEGORY_RULES if r.category == 'zip']
        _, name = mkztemp('test', name_rules=rules)

        zf = zipfile.ZipFile(name)
        assert zf.namelist() == ['test/test.png', 'test/index.html']


def test_zip():
    runner = CliRunner()
    with runner.isolated_filesystem():
        token = authenticate(
            os.environ['KUDU_USERNAME'], os.environ['KUDU_PASSWORD']
        )
        creation_time = api_request(
            'get', '/files/%d/' % 519655, token=token
        ).json()['creationTime']

        open('index.html', 'a').close()
        open('thumbnail.png', 'a').close()
        result = runner.invoke(cli, ['push', '-f', 519655])
        assert result.exit_code == 0

        result = runner.invoke(cli, ['pull', '-f', 519655])
        assert result.exit_code == 0
        assert exists('index.html')
        assert exists('thumbnail.png')
        assert creation_time != api_request(
            'get', '/files/%d/' % 519655, token=token
        ).json()['creationTime']


def test_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        json_txt = '{"time": %d}' % time.time()

        with open('upload.json', 'w+t') as fh:
            fh.write(json_txt)

        result = runner.invoke(cli, ['push', '-f', 703251, '-p', 'upload.json'])
        assert result.exit_code == 0

        result = runner.invoke(cli, ['pull', '-f', 703251])
        assert result.exit_code == 0

        with open('-LsHlYKFuqKEO4VxS2fT.json', 'r+t') as fh:
            assert json_txt == fh.read()
