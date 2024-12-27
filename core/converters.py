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

from collections import deque
from typing import NamedTuple

from discord.ext import commands

from core.context import Context

__all__ = ("Codeblock", "CodeblockConverter")


class Codeblock(NamedTuple):
    language: str | None
    content: str


class CodeblockConverter(commands.Converter[Codeblock]):
    """
    A codeblock converter subclassed from :class:`commands.Converter`.
    Will return a namedtuple of :attr:`Codeblock.language` (```<lang>) and the codeblock content.
    :attr:`Codeblock.language` will be ``None`` if the input was not a complete codeblock.
    """

    async def convert(self, ctx: Context, argument: str) -> Codeblock:  # pyright: ignore[reportIncompatibleMethodOverride] # generic narrowing on Context
        if not argument.startswith("`"):
            return Codeblock(None, argument)

        # store a small deque of the previous characters.
        previous_characters: deque[str] = deque(maxlen=3)
        backticks = 0
        within_language = False
        within_code = False
        language: list[str] = []
        code: list[str] = []

        for character in argument:
            if character == "`" and not within_code and not within_language:
                backticks += 1
            if (previous_characters and previous_characters[-1] == "`" and character != "`") or (
                within_code and "".join(previous_characters) != "`" * backticks
            ):
                within_code = True
                code.append(character)
            if character == "\n":
                within_language = False
                within_code = True
            elif "".join(previous_characters) == "`" * 3 and character != "`":
                within_language = True
                language.append(character)
            elif within_language:
                if character != "\n":
                    language.append(character)

            previous_characters.append(character)

        if not code and not language:
            code[:] = previous_characters

        return Codeblock("".join(language), "".join(code[len(language) : -backticks]))
