class KuduException(Exception):
    def __str__(self):
        return '%s: %s' % (type(self).__name__, self.message)


class InvalidPath(KuduException):
    pass


class InvalidAuth(KuduException):
    pass


class NotFound(KuduException):
    pass


class NotAuthorized(KuduException):
    pass


class FileNotFound(KuduException):
    pass


class ConfigError(KuduException):
    pass


class UnknownProvider(KuduException):
    pass


class BranchNotPermitted(KuduException):
    pass


class PathNotPermitted(KuduException):
    pass


class ConnectionError(KuduException):
    pass
