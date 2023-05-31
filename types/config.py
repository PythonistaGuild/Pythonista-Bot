from typing import TypedDict

__all__ = ("Config",)


class APITokens(TypedDict):
    riot: str


class Database(TypedDict):
    user: str
    password: str
    host: str
    port: int
    database: str


class Bot(TypedDict):
    token: str
    webhook_url: str
    prefix: str


class Config(TypedDict):
    BOT: Bot
    DATABASE: Database
    API_TOKENS: APITokens
