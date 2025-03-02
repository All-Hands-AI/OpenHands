from pydantic import BaseModel


class GitLabUser(BaseModel):
    id: int | None = None
    username: str | None = None
    avatar_url: str | None = None
    name: str | None = None
    email: str | None = None
    organization: str | None = None


class GlAuthenticationError(Exception):
    pass


class GLUnknownException(Exception):
    pass