class PatchingException(Exception):
    pass


class HunkException(PatchingException):
    def __init__(self, msg, hunk=None):
        self.hunk = hunk
        if hunk is not None:
            super(HunkException, self).__init__(
                '{msg}, in hunk #{n}'.format(msg=msg, n=hunk)
            )
        else:
            super(HunkException, self).__init__(msg)


class ApplyException(PatchingException):
    pass


class SubprocessException(ApplyException):
    def __init__(self, msg, code):
        super(SubprocessException, self).__init__(msg)
        self.code = code


class HunkApplyException(HunkException, ApplyException, ValueError):
    pass


class ParseException(HunkException, ValueError):
    pass
