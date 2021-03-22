from os.path import exists, join
from zipfile import ZipFile

from click.testing import CliRunner

from kudu.__main__ import cli
from kudu.config import write_config


def test_interface():
    runner = CliRunner()
    with runner.isolated_filesystem():
        write_config({'file_id': 527702})
        result = runner.invoke(cli, ['pull'])
        assert result.exit_code == 0
        assert exists(join('interface', 'index.html'))
        assert exists(join('interface_1', 'index.html'))
        assert exists(join('lang', 'AR.csv'))


def test_json_path():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['pull', '-f', 519631, '-p', 'test.json'])
        assert result.exit_code == 0
        assert exists('test.json')


def test_zip():
    runner = CliRunner()
    with runner.isolated_filesystem():
        write_config({'file_id': 519629})
        result = runner.invoke(cli, ['pull'])
        assert result.exit_code == 0
        assert exists('index.html')
        assert exists('thumbnail.png')
        assert exists(join('folder', 'foobar.json'))


def test_zip_path():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['pull', '-f', 519629, '-p', 'test.zip'])
        assert result.exit_code == 0
        assert exists('test.zip')

        zip_file = ZipFile('test.zip')
        assert zip_file.testzip() is None
