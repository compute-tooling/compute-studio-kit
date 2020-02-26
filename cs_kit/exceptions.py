class CSKitException(Exception):
    pass


class CSKitError(CSKitException):
    pass


class SerializationError(CSKitException):
    pass


class APIException(CSKitException):
    pass
