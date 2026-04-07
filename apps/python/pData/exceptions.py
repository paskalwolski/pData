class BoundaryExceeded(BaseException):
    pass

class SessionBoundaryExceeded(BoundaryExceeded):
    pass    

class InvalidBundle(ValueError):
    pass