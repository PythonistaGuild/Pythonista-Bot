from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

import discord
from discord.ext import commands

from constants import GUILD_ID, Roles


if TYPE_CHECKING:
    from .bot import Bot


__all__ = (
    "Context",
    "GuildContext",
    "Interaction",
)


Interaction: TypeAlias = discord.Interaction["Bot"]


class Context(commands.Context["Bot"]):
    @discord.utils.cached_property
    def replied_reference(self) -> discord.MessageReference | None:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved.to_reference()
        return None

    @discord.utils.cached_property
    def replied_message(self) -> discord.Message | None:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved
        return None

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

        roles = member._roles  # type: ignore # we know this won't change for a while
        return roles.has(Roles.ADMIN) or roles.has(Roles.MODERATOR)


class GuildContext(Context):
    guild: discord.Guild  # type: ignore # type lie due to narrowing
    author: discord.Member  # type: ignore # type lie due to narrowing
