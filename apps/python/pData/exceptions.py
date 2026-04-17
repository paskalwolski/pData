class BoundaryExceeded(BaseException):
    pass

class SessionBoundaryExceeded(BoundaryExceeded):
    pass    

class LapBoundaryExceeded(BoundaryExceeded):
    pass    

class InvalidBundle(ValueError):
    pass