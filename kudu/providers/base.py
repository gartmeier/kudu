import StringIO
import os
import tempfile

import paramiko

from kudu.exceptions import ConnectionError


class BaseProvider(object):
    logger = None

    def __init__(self, logger=None):
        self.logger = logger

    def deploy(self, **kwargs):
        raise NotImplementedError()

    def log_info(self, message):
        if self.logger:
            self.logger.info(message)

    def log_error(self, message):
        if self.logger:
            self.logger.error(message)


# TODO share storage for token and pkfile
def get_pkfile_file(address):
    return os.path.join(tempfile.gettempdir(), 'kudu_pkey_' + address.replace('.', '_'))


def restore_pkfile(address):
    path = get_pkfile_file(address)
    if os.path.isfile(path):
        with open(path, 'r') as fh:
            return fh.read()


def save_pkfile(address, pkfile):
    path = get_pkfile_file(address)
    with open(path, 'w') as fh:
        return fh.write(pkfile)


class SftpProvider(BaseProvider):
    name = 'sftp'

    def deploy(self, address, username, password=None,
               remote_path=None, local_path=None, files=None, logger=None):
        pkfile = restore_pkfile(address)

        if not pkfile:
            pkfile_default = '~/.ssh/id_dsa'
            pkfile = raw_input('Identity file (private key) [%s]: ' % pkfile_default)

            if not pkfile:
                pkfile = pkfile_default

            pkfile = os.path.expanduser(pkfile)

        if not os.path.exists(pkfile):
            logger.warning('Identity file %s not accessible: No such file or directory.' % pkfile)

        if os.path.exists(pkfile):
            with open(pkfile, 'r') as fh:
                pk_str = fh.read()

            pkey_io = StringIO.StringIO(pk_str)
            pkey = paramiko.RSAKey.from_private_key(pkey_io)
        else:
            pkey = None

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(address, username=username, pkey=pkey)
        except paramiko.SSHException as e:
            raise ConnectionError(e.message)

        save_pkfile(address, pkfile)

        sftp = ssh.open_sftp()

        for file in files:
            sftp.put(file['local_path'], file['remote_path'])

        sftp.close()
        ssh.close()
