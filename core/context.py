from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

import discord
from discord.ext import commands
from constants import GUILD_ID, Roles


if TYPE_CHECKING:
    from bot import Bot

__all__ = (
    "Context",
    "GuildContext",
    "Interaction",
)

Interaction: TypeAlias = discord.Interaction["Bot"]


class Context(commands.Context["Bot"]):
    bot: Bot

    def author_is_mod(self) -> bool:
        member: discord.Member
        if self.guild is None:  # dms
            guild = self.bot.get_guild(GUILD_ID)
            if not guild:
                return False

            _member = guild.get_member(self.author.id)
            if _member is not None:
                member = _member

            else:
                return False

        else:
            member = self.author  # type: ignore

        roles = member._roles
        return roles.has(Roles.ADMIN) or roles.has(Roles.MODERATOR)

    @discord.utils.copy_doc(commands.Context.reply)
    async def reply(self, content: str, **kwargs) -> discord.Message:
        if "mention_author" not in kwargs:
            kwargs["mention_author"] = False

        return await super().reply(content, **kwargs)



class GuildContext(Context):
    guild: discord.Guild  # type: ignore # type lie due to narrowing
    author: discord.Member  # type: ignore # type lie due to narrowing
