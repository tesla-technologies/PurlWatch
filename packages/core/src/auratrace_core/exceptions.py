class AuratraceError(Exception):
    exit_code = 1


class InputError(AuratraceError):
    exit_code = 2


class OfflineMissError(AuratraceError):
    exit_code = 3


class NetworkError(AuratraceError):
    exit_code = 4
