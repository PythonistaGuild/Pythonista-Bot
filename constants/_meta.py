"""MIT License

Copyright (c) 2021-Present PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NoReturn, cast

import toml

if TYPE_CHECKING:
    from types_.config import Database, Logging, Tokens


_config = toml.load("config.toml")


class ConstantsMeta(type):
    def __new__(mcs, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        if name == "CONSTANTS":
            return super().__new__(mcs, name, bases, attrs)

        try:
            section = cast("Tokens | Database | Logging", _config[name.upper()])
        except KeyError:
            return super().__new__(mcs, name, bases, attrs)

        for option, value in section.items():
            if option in attrs:
                attrs[option] = value

        return super().__new__(mcs, name, bases, attrs)

    def __setattr__(self, attr: str, nv: Any) -> NoReturn:
        msg = f"Constant <{attr}> cannot be assigned to."
        raise RuntimeError(msg)

    def __delattr__(self, attr: str) -> NoReturn:
        msg = f"Constant <{attr}> cannot be deleted."
        raise RuntimeError(msg)


class CONSTANTS(metaclass=ConstantsMeta):
    pass
