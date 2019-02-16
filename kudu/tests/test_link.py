import ctypes
import os
import shutil
import tempfile
import thread
import time
from os.path import join, exists

from click.testing import CliRunner

from kudu.__main__ import cli
from kudu.config import write_config


def terminate_thread(thread_id):
    exc = ctypes.py_object(KeyboardInterrupt)
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), exc)


def test_initial_copyfiles():
    dirpath = os.path.join(tempfile.gettempdir(), str(time.time()))
    os.mkdir(dirpath)

    runner = CliRunner()
    with runner.isolated_filesystem():
        open('index.html', 'a').close()

        thread_id = thread.start_new_thread(runner.invoke, (cli, ['link', '-f', 524689, '-p', dirpath]))
        time.sleep(2)

        terminate_thread(thread_id)

    assert exists(join(dirpath, 'zip', '524689_1550305880612', 'index.html'))
    shutil.rmtree(dirpath)


def test_subsequent_create_file():
    dirpath = os.path.join(tempfile.gettempdir(), str(time.time()))
    os.mkdir(dirpath)

    runner = CliRunner()
    with runner.isolated_filesystem():
        thread_id = thread.start_new_thread(runner.invoke, (cli, ['link', '-f', 524689, '-p', dirpath]))
        time.sleep(2)

        open('index.html', 'a').close()
        time.sleep(1)

        terminate_thread(thread_id)

    assert exists(join(dirpath, 'zip', '524689_1550305880612', 'index.html'))
    shutil.rmtree(dirpath)


def test_subsequent_move_file():
    dirpath = os.path.join(tempfile.gettempdir(), str(time.time()))
    os.mkdir(dirpath)

    runner = CliRunner()
    with runner.isolated_filesystem():
        open('index.html', 'a').close()

        thread_id = thread.start_new_thread(runner.invoke, (cli, ['link', '-f', 524689, '-p', dirpath]))
        time.sleep(2)

        os.rename('index.html', 'moved.html')
        time.sleep(1)

        terminate_thread(thread_id)

    assert exists(join(dirpath, 'zip', '524689_1550305880612', 'moved.html'))
    shutil.rmtree(dirpath)


def test_subsequent_modify_file():
    dirpath = os.path.join(tempfile.gettempdir(), str(time.time()))
    os.mkdir(dirpath)

    runner = CliRunner()
    with runner.isolated_filesystem():
        open('index.html', 'a').close()

        thread_id = thread.start_new_thread(runner.invoke, (cli, ['link', '-f', 524689, '-p', dirpath]))
        time.sleep(2)

        with open('index.html', 'wb') as stream:
            stream.write('test')
        time.sleep(1)

        terminate_thread(thread_id)

    dst = join(dirpath, 'zip', '524689_1550305880612', 'index.html')
    assert exists(dst)

    with open(dst, 'rb') as stream:
        assert stream.read() == 'test'

    shutil.rmtree(dirpath)
