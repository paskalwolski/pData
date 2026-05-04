class BoundaryExceeded(BaseException):
    pass


class SessionBoundaryExceeded(BoundaryExceeded):
    pass


class LapBoundaryExceeded(BoundaryExceeded):
    pass


class InvalidBundle(ValueError):
    pass


class APIException(BaseException):
    pass

class ACException(BaseException):
    pass
