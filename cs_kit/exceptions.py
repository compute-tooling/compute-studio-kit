import json


class CSKitException(Exception):
    def __init__(self, msg, owner=None, title=None):
        self.msg = msg
        self.owner = owner
        self.title = title

        try:
            dumped = json.dumps(msg, indent=4)
        except json.JSONDecodeError:
            dumped = str(msg)
        super().__init__(dumped)


class CSKitError(CSKitException):
    pass


class SerializationError(CSKitException):
    pass


class APIException(CSKitException):
    pass
