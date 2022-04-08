from os import mkdir

from click.testing import CliRunner

from kudu.__main__ import cli
from kudu.config import write_config


def test_interface():
    runner = CliRunner()
    with runner.isolated_filesystem():
        write_config({"file_id": 1105408})

        mkdir("interface")

        with open("interface/index.html", "a") as f:
            f.write("<html></html>")

        result = runner.invoke(cli, ["push"])
        assert result.exit_code == 0


def test_zip():
    runner = CliRunner()
    with runner.isolated_filesystem():
        open("index.html", "a").close()
        open("thumbnail.png", "a").close()
        result = runner.invoke(cli, ["push", "-f", 519655])
        assert result.exit_code == 0


def test_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        open("upload.json", "a").close()
        result = runner.invoke(cli, ["push", "-f", 703251, "-p", "upload.json"])
        assert result.exit_code == 0
