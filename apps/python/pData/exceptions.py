class BoundaryExceeded(BaseException):
    def __init__(self, reason=None, *args):
        # type: (str | None, object) -> None
        self.reason = reason
        super().__init__(*args)


class SessionBoundaryExceeded(BoundaryExceeded):
    pass


class LapBoundaryExceeded(BoundaryExceeded):
    pass


class InvalidBundle(ValueError):
    pass
