from typing import NotRequired, TypedDict


__all__ = ("Config",)


class Tokens(TypedDict):
    bot: str
    idevision: str
    mystbin: str
    github_bot: str
    pythonista: str


class Database(TypedDict):
    dsn: str


class Logging(TypedDict):
    webhook_url: NotRequired[str]
    webhook_avatar_url: NotRequired[str]
    level: int


class Snekbox(TypedDict):
    url: str


class BadBin(TypedDict):
    domains: list[str]

class Config(TypedDict):
    prefix: str
    owner_ids: NotRequired[list[int]]
    TOKENS: Tokens
    DATABASE: Database
    LOGGING: Logging
    SNEKBOX: NotRequired[Snekbox]
    BADBIN: BadBin
