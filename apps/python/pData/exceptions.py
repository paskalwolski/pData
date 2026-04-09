class BoundaryExceeded(BaseException):
    def __init__(self, reason, *args):
        # type: (str, object) -> None
        self.reason = reason
        super().__init__(*args)
    pass

class SessionBoundaryExceeded(BoundaryExceeded):
    pass    

class LapBoundaryExceeded(BoundaryExceeded):
    pass    

class InvalidBundle(ValueError):
    pass