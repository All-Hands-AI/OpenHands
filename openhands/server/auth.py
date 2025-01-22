from fastapi import Request


def get_user_id(request: Request) -> str | None:
    return getattr(request.state, 'github_user_id', None)
