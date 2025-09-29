class OpenHandsError(Exception):
    pass


class AuthError(OpenHandsError):
    """Error in authentication"""


class PermissionsError(OpenHandsError):
    """Error in permissions"""


class SandboxError(OpenHandsError):
    """Error in Sandbox"""
