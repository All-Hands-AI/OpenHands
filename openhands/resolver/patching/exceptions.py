class PatchingException(Exception):
    pass


class HunkException(PatchingException):
    def __init__(self, msg: str, hunk: int | None = None) -> None:
        self.hunk = hunk
        if hunk is not None:
            super().__init__('{msg}, in hunk #{n}'.format(msg=msg, n=hunk))
        else:
            super().__init__(msg)


class ApplyException(PatchingException):
    pass


class SubprocessException(ApplyException):
    def __init__(self, msg: str, code: int) -> None:
        super().__init__(msg)
        self.code = code


class HunkApplyException(HunkException, ApplyException, ValueError):
    pass


class ParseException(HunkException, ValueError):
    pass
