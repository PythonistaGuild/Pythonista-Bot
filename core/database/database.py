"""The MIT License (MIT)

Copyright (c) 2020 PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
import asyncpg

from core.core import CONFIG


class Database:

    _pool: asyncpg.pool.Pool

    @classmethod
    async def __ainit__(cls) -> None:
        settings = CONFIG['DATABASE']
        dsn = f'postgres://{settings["user"]}:{settings["password"]}@{settings["host"]}:{settings["port"]}/' \
              '{database}'

        try:
            cls._pool = await asyncpg.create_pool(dsn.format(database=settings['database']))
        except asyncpg.InvalidCatalogNameError:
            temp = await asyncpg.connect(dsn.format(database='template1'))
            await temp.execute(f"""CREATE DATABASE {settings['database']} OWNER {settings['user']}""")

            await temp.close()
            cls._pool = await asyncpg.create_pool(dsn.format(database=settings['database']))

        with open('core/database/schema.sql') as schema:
            async with cls._pool.acquire() as connection:
                await connection.execute(schema.read())
