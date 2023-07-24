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
import random

from discord import Colour
from discord.utils import escape_markdown


__all__ = (
    "to_codeblock",
    "random_pastel_colour",
)


def to_codeblock(
    content: str,
    language: str = "py",
    replace_existing: bool = True,
    escape_md: bool = True,
    new: str = "'''",
):
    """
    Quick function to put our content into a Discord accepted codeblock.
    """
    if replace_existing:
        content = content.replace("```", new)
    if escape_md:
        content = escape_markdown(content)
    return f"```{language}\n{content}\n```"


def random_pastel_colour() -> Colour:
    return Colour.from_hsv(random.random(), 0.28, 0.97)
