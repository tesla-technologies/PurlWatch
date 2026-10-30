class AuratraceError(Exception):
    exit_code = 1


class InputError(AuratraceError):  # SBOM, PURL, configuración
    exit_code = 2


class OfflineMissError(AuratraceError):  # el snapshot no tiene el documento
    exit_code = 3


class NetworkError(AuratraceError):  # tras agotar reintentos
    exit_code = 4
