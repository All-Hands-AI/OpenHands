from dataclasses import dataclass


@dataclass
class GitHubUser:
    id: int
    login: str
    avatar_url: str
    company: str | None = None
    name: str | None = None
    email: str | None = None


@dataclass
class GitHubRepository:
    id: int
    full_name: str
    stargazers_count: int | None = None
    link_header: str | None = None
