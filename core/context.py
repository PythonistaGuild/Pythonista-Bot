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
    def replied_reference(self) -> discord.MessageReference | discord.Message:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved.to_reference(fail_if_not_exists=False)
        return self.message

    @discord.utils.cached_property
    def replied_message(self) -> discord.Message:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved
        return self.message

    def author_is_mod(self) -> bool:
        member: discord.Member | None

        if self.guild is None:  # dms
            guild = self.bot.get_guild(GUILD_ID)

            if not guild:
                return False

            member = guild.get_member(self.author.id)
            if member is None:
                return False

        else:
            member = self.author  # pyright: ignore[reportAssignmentType] # type lie for a shortcut

        roles = member._roles  # pyright: ignore[reportPrivateUsage,reportOptionalMemberAccess] # we know this won't change for a while
        return roles.has(Roles.ADMIN) or roles.has(Roles.MODERATOR)


class GuildContext(Context):
    guild: discord.Guild  # pyright: ignore[reportIncompatibleVariableOverride] # type lie due to narrowing
    author: discord.Member  # pyright: ignore[reportIncompatibleVariableOverride] # type lie due to narrowing
