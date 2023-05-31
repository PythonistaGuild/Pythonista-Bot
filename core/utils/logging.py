from __future__ import annotations

import logging
import pathlib
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING, Any, Mapping

from discord.utils import (
    _ColourFormatter as ColourFormatter,  # type: ignore # shh, I need it
)
from discord.utils import stream_supports_colour

if TYPE_CHECKING:
    from logging import _ExcInfoType  # type: ignore # shh, I need it

    from typing_extensions import Self


class LogHandler:
    def __init__(self, *, stream: bool = True) -> None:
        self.log: logging.Logger = logging.getLogger()
        self.max_bytes: int = 32 * 1024 * 1024
        self.logging_path = pathlib.Path("./logs/")
        self.logging_path.mkdir(exist_ok=True)
        self.stream: bool = stream

    async def __aenter__(self) -> Self:
        return self.__enter__()

    def __enter__(self: Self) -> Self:
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.INFO)

        self.log.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            filename=self.logging_path / "Mipha.log",
            encoding="utf-8",
            mode="w",
            maxBytes=self.max_bytes,
            backupCount=5,
        )
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        fmt = logging.Formatter(
            "[{asctime}] [{levelname:<7}] {name}: {message}", dt_fmt, style="{"
        )
        handler.setFormatter(fmt)
        self.log.addHandler(handler)

        if self.stream:
            stream_handler = logging.StreamHandler()
            if stream_supports_colour(stream_handler):
                stream_handler.setFormatter(ColourFormatter())
            self.log.addHandler(stream_handler)

        return self

    async def __aexit__(self, *args: Any) -> None:
        return self.__exit__(*args)

    def __exit__(self, *args: Any) -> None:
        handlers = self.log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            self.log.removeHandler(hdlr)

    def debug(
        self,
        message: object,
        *args: Any,
        exc_info: _ExcInfoType,
        stack_info: bool = False,
        stack_level: int = 1,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        self.log.debug(
            msg=message,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stack_level,
            extra=extra,
        )

    def info(
        self,
        message: object,
        *args: Any,
        exc_info: _ExcInfoType,
        stack_info: bool = False,
        stack_level: int = 1,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        self.log.info(
            msg=message,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stack_level,
            extra=extra,
        )

    def warning(
        self,
        message: object,
        *args: Any,
        exc_info: _ExcInfoType,
        stack_info: bool = False,
        stack_level: int = 1,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        self.log.warning(
            msg=message,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stack_level,
            extra=extra,
        )

    def error(
        self,
        message: object,
        *args: Any,
        exc_info: _ExcInfoType,
        stack_info: bool = False,
        stack_level: int = 1,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        self.log.warning(
            msg=message,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stack_level,
            extra=extra,
        )

    def critical(
        self,
        message: object,
        *args: Any,
        exc_info: _ExcInfoType,
        stack_info: bool = False,
        stack_level: int = 1,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        self.log.critical(
            msg=message,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stack_level,
            extra=extra,
        )
