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

import asyncio

import aiohttp
import asyncpg
import mystbin
import uvicorn

import core
from core.utils import LogHandler
from modules import EXTENSIONS
from server.application import Application

tasks: set[asyncio.Task[None]] = set()


async def main() -> None:
    async with (
        core.Bot() as bot,
        aiohttp.ClientSession() as session,
        asyncpg.create_pool(dsn=core.CONFIG["DATABASE"]["dsn"]) as pool,
        LogHandler(bot=bot) as handler,
    ):
        bot.logging_queue = asyncio.Queue()
        bot.strip_after_prefix = True
        bot.case_insensitive = True
        bot.session = session
        bot.pool = pool
        bot.log_handler = handler

        _mystbin_token = core.CONFIG["TOKENS"]
        bot.mb_client = mystbin.Client(session=session)

        await bot.load_extension("jishaku")
        for extension in EXTENSIONS:
            await bot.load_extension(extension.name)

            bot.log_handler.log.info(
                "Loaded %sextension: %s",
                "module " if extension.ispkg else "",
                extension.name,
            )

        server_config = core.CONFIG.get("WEBSERVER")
        if server_config:
            app: Application = Application(bot=bot)
            config: uvicorn.Config = uvicorn.Config(app, host=server_config["host"], port=server_config["port"])
            server: uvicorn.Server = uvicorn.Server(config)

            tasks.add(asyncio.create_task(bot.start(core.CONFIG["TOKENS"]["bot"])))
            await server.serve()
        else:
            await bot.start(core.CONFIG["TOKENS"]["bot"])


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Fix this later, but you killed bot with KeyboardInterrupt...")
