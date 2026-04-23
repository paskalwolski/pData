class BoundaryExceeded(BaseException):
    def __init__(
        self,
        *args,
        reason=None,
    ):
        # type: (str | None, object) -> None
        self.reason = reason
        super().__init__(*args)


class SessionBoundaryExceeded(BoundaryExceeded):
    pass


class LapBoundaryExceeded(BoundaryExceeded):
    pass


class InvalidBundle(ValueError):
    pass


class APIException(BaseException):
    pass
