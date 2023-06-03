from typing import NotRequired, TypedDict


__all__ = ("Config",)


class Tokens(TypedDict):
    bot: str
    idevision: str
    mystbin: str


class Database(TypedDict):
    dsn: str


class Logging(TypedDict):
    webhook_url: str
    level: int


class Snekbox(TypedDict):
    url: str


class Config(TypedDict):
    prefix: str
    TOKENS: Tokens
    DATABASE: Database
    LOGGING: Logging
    SNEKBOX: NotRequired[Snekbox]