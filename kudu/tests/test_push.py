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

        rules = [r.rule for r in CATEGORY_RULES if '' in r.category]
        _, name = mkztemp('interface_test', name_rules=rules)

        zf = zipfile.ZipFile(name)
        namelist = zf.namelist()
        assert namelist == ['interface_test/index.html']

    with runner.isolated_filesystem():
        open('index.html', 'a').close()
        open('thumbnail.png', 'a').close()

        rules = [r.rule for r in CATEGORY_RULES if 'zip' in r.category]
        _, name = mkztemp('test', name_rules=rules)

        zf = zipfile.ZipFile(name)
        namelist = zf.namelist()
        assert len(namelist) == 2
        assert 'test/test.png' in namelist
        assert 'test/index.html' in namelist


def test_zip():
    runner = CliRunner()
    with runner.isolated_filesystem():
        open('index.html', 'a').close()
        open('thumbnail.png', 'a').close()
        result = runner.invoke(cli, ['push', '-f', 519655])
        assert result.exit_code == 0


def test_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        open('upload.json', 'a').close()
        result = runner.invoke(cli, ['push', '-f', 703251, '-p', 'upload.json'])
        assert result.exit_code == 0
