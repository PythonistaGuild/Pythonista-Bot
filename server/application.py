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
from typing import Any

import starlette_plus

from core.bot import Bot
from core.core import CONFIG


class Application(starlette_plus.Application):

    def __init__(self, *, bot: Bot) -> None:
        self.bot: Bot = bot
        self.__auth: str | None = CONFIG["TOKENS"].get("pythonista")

        super().__init__()

    @starlette_plus.route("/dpy/modlog", methods=["POST"], prefix=False, include_in_schema=False)
    async def dpy_modlog(self, request: starlette_plus.Request) -> starlette_plus.Response:
        if not self.__auth:
            return starlette_plus.Response("Unable to process request: Missing Auth (Server)", status_code=503)

        auth: str | None = request.headers.get("authorization", None)
        if not auth:
            return starlette_plus.Response("Forbidden", status_code=403)

        if auth != self.__auth:
            return starlette_plus.Response("Unauthorized", status_code=401)

        try:
            data: dict[str, Any] = await request.json()
        except Exception as e:
            return starlette_plus.Response(f"Invalid payload: {e}", status_code=400)

        if not data:
            return starlette_plus.Response("Invalid payload: Empty payload provided", status_code=400)

        self.bot.dispatch("papi_dpy_modlog", data)
        return starlette_plus.Response(status_code=204)
