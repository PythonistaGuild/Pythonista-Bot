from __future__ import annotations

import logging
import pathlib
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING, Any

from discord.utils import _ColourFormatter as ColourFormatter, stream_supports_colour  # type: ignore # shh, I need it

import core


if TYPE_CHECKING:
    from typing_extensions import Self

    from core import Bot


class QueueEmitHandler(logging.Handler):
    def __init__(self, bot: Bot, /) -> None:
        self.bot: Bot = bot
        super().__init__(logging.INFO)

    def emit(self, record: logging.LogRecord) -> None:
        self.bot.logging_queue.put_nowait(record)


class PAPILoggingFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__(name="modules.api")

    def filter(self, record: logging.LogRecord) -> bool:
        return not ("Received HELLO" in record.msg or "added our subscription" in record.msg)


class LogHandler:
    def __init__(self, *, bot: Bot, stream: bool = True) -> None:
        self.log: logging.Logger = logging.getLogger()
        self.max_bytes: int = 32 * 1024 * 1024
        self.logging_path = pathlib.Path("./logs/")
        self.logging_path.mkdir(exist_ok=True)
        self.stream: bool = stream
        self.bot: Bot = bot
        self.debug = self.log.debug
        self.info = self.log.info
        self.warning = self.log.warning
        self.error = self.log.error
        self.critical = self.log.critical

    async def __aenter__(self) -> Self:
        return self.__enter__()

    def __enter__(self: Self) -> Self:
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.INFO)
        logging.getLogger("discord.state").setLevel(logging.WARNING)
        logging.getLogger("discord.gateway").setLevel(logging.WARNING)
        logging.getLogger("modules.api").addFilter(PAPILoggingFilter())

        self.log.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            filename=self.logging_path / "PythonistaBot.log",
            encoding="utf-8",
            mode="w",
            maxBytes=self.max_bytes,
            backupCount=5,
        )
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        fmt = logging.Formatter("[{asctime}] [{levelname:<7}] {name}: {message}", dt_fmt, style="{")
        handler.setFormatter(fmt)
        self.log.addHandler(handler)

        if self.stream:
            stream_handler = logging.StreamHandler()
            if stream_supports_colour(stream_handler):
                stream_handler.setFormatter(ColourFormatter())
            self.log.addHandler(stream_handler)
        if core.CONFIG["LOGGING"].get("webhook_url"):
            self.log.addHandler(QueueEmitHandler(self.bot))

        return self

    async def __aexit__(self, *args: Any) -> None:
        return self.__exit__(*args)

    def __exit__(self, *args: Any) -> None:
        handlers = self.log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            self.log.removeHandler(hdlr)
