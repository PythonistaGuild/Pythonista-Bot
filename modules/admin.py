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

import logging

from discord.ext import commands

import core
from constants import GUILD_ID
from core.context import Context

LOGGER = logging.getLogger(__name__)


class Administration(commands.Cog):
    def __init__(self, bot: core.Bot, /) -> None:
        self.bot: core.Bot = bot
        if owners := core.CONFIG.get("owner_ids"):
            LOGGER.info("[Ownership] Setting new owners to:\n%s", ", ".join([str(o) for o in owners]))
            bot.loop.create_task(self.populate_owners(owners))

    async def cog_check(self, ctx: Context) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]  # maybecoro override woes
        return await self.bot.is_owner(ctx.author)

    async def populate_owners(self, owner_ids: list[int]) -> None:
        await self.bot.wait_until_ready()

        new_owners: list[int] = []
        for id_ in owner_ids:
            user = self.bot.get_user(id_)
            if user:
                LOGGER.info("[Ownership] New User found for owner: %s (%s)", str(user), user.id)
                new_owners.append(id_)
                continue

            guild = self.bot.get_guild(GUILD_ID)
            if not guild:
                continue

            role = guild.get_role(id_)
            if role:
                LOGGER.info("[Ownership] New Role found for owner: %s (%s)", str(role), role.id)
                new_owners += [m.id for m in role.members]
                continue

        if new_owners:
            self.bot.owner_id = None
            self.bot.owner_ids = set(new_owners)


async def setup(bot: core.Bot) -> None:
    await bot.add_cog(Administration(bot))
