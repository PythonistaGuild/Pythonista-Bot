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
from .meta import CONSTANTS


__all__ = ('Roles', )


class Roles(CONSTANTS):

    # Human
    ADMIN: int = 490952483238313995
    MODERATOR: int = 578255729295884308
    KNOWLEDGEABLE: int = 490994825315745795
    PYTHONISTA_DEVELOPER: int = 763106310098911263
    HELPER: int = 649520971069390858
    CONTRIBUTOR: int = 763106223457304607

    # Bots
    ADMIN_BOT: int = 490952487122108441
    GUILD_BOT: int = 570452583932493825
    TEST_BOT: int = 490954992384081930
