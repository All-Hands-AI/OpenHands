import os
import shutil
import tempfile
from types import MethodType


def _rmtree(cls, name, ignore_errors=False):
    def onerror(func, path, exc_info):
        if issubclass(exc_info[0], PermissionError):

            def resetperms(path):
                try:
                    if os.chflags in os.supports_follow_symlinks:  # This is the patch
                        os.chflags(path, 0, follow_symlinks=False)  # This is the patch
                    elif not os.path.islink(path):  # This is the patch
                        os.chflags(path, 0)
                except AttributeError:
                    pass
                if os.chmod in os.supports_follow_symlinks:  # This is the patch
                    os.chmod(path, 0o700, follow_symlinks=False)  # This is the patch
                elif not os.path.islink(path):  # This is the patch
                    os.chmod(path, 0o700)

            try:
                if path != name:
                    resetperms(os.path.dirname(path))
                resetperms(path)

                try:
                    os.unlink(path)
                # PermissionError is raised on FreeBSD for directories
                except (IsADirectoryError, PermissionError):
                    cls._rmtree(path, ignore_errors=ignore_errors)
            except FileNotFoundError:
                pass
        elif issubclass(exc_info[0], FileNotFoundError):
            pass
        else:
            if not ignore_errors:
                raise

    shutil.rmtree(name, onerror=onerror)


# Monkey patch the class method tempfile.TemporaryDirectory._rmtree
tempfile.TemporaryDirectory._rmtree = MethodType(_rmtree, tempfile.TemporaryDirectory)
