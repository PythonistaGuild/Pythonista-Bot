"""MIT License

Copyright (c) 2020 PythonistaGuild

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
from discord.utils import escape_markdown


__all__ = ('to_codeblock', )


def to_codeblock(content, language='py', *, replace_existing=True, escape_md=True, new="'''"):
    """Quick function to put our content into a Discord accepted codeblock.

    Parameters
    -----------
    content: :class:`str`
        The content of the codeblock.
    language: :class:`str`
        The language to pass to the codeblock for syntax highlighting.
    replace_existing: :class:`bool`
        Toggle to replace an 'inner' codeblock's triple backticks with the string is passed to :param:`new`
    escape_md: :class:`bool`
        Toggle to escape the inner markdown of the content.
    new: :class:`str`
        The string to replace the inner codeblock's triple backticks with.
    """
    if replace_existing:
        content = content.replace('```', new)
    if escape_md:
        content = escape_markdown(content)
    content = content or "<<Eval returned no output.>>"
    return f'```{language}\n{content}\n```'
