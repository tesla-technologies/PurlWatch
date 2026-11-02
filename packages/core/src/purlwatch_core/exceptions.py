class PurlwatchError(Exception):
    exit_code = 1


class InputError(PurlwatchError):
    exit_code = 2


class OfflineMissError(PurlwatchError):
    exit_code = 3


class NetworkError(PurlwatchError):
    exit_code = 4
