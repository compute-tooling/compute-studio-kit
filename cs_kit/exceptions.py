import json


class CSKitException(Exception):
    def __init__(self, msg):
        super().__init__(json.dumps(msg, indent=4))


class CSKitError(CSKitException):
    pass


class SerializationError(CSKitException):
    pass


class APIException(CSKitException):
    pass
