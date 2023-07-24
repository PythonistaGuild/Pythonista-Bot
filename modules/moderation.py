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
from __future__ import annotations

import asyncio
import base64
import binascii
import datetime
import re
from textwrap import shorten
from typing import TYPE_CHECKING, Any, Self, TypeAlias

import discord
import yarl
from discord.ext import commands

import core
from constants import Channels
from core.context import Interaction
from core.utils import random_pastel_colour


if TYPE_CHECKING:
    from types_.papi import ModLogPayload, PythonistaAPIWebsocketPayload

    ModLogType: TypeAlias = PythonistaAPIWebsocketPayload[ModLogPayload]

TOKEN_RE = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}")
PROSE_LOOKUP = {
    1: "banned",
    2: "kicked",
    3: "muted",
    4: "unbanned",
    5: "helpblocked",
}


def validate_token(token: str) -> bool:
    try:
        # Just check if the first part validates as a user ID
        (user_id, _, _) = token.split(".")
        user_id = int(base64.b64decode(user_id + "==", validate=True))
    except (ValueError, binascii.Error):
        return False
    return True


class GithubError(commands.CommandError):
    pass


class ModerationRespostView(discord.ui.View):
    message: discord.Message | discord.WebhookMessage

    def __init__(self, *, timeout: float | None = 180, target_id: int, target_reason: str) -> None:
        super().__init__(timeout=timeout)
        self.target: discord.Object = discord.Object(id=target_id, type=discord.Member)
        self.target_reason: str = target_reason

    def _disable_all_buttons(self) -> None:
        for item in self.children:
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                item.disabled = True

    async def on_timeout(self) -> None:
        self._disable_all_buttons()
        await self.message.edit(view=self)

    @discord.ui.button(label="Ban", emoji="\U0001f528")
    async def ban_button(self, interaction: Interaction, button: discord.ui.Button[Self]) -> None:
        assert interaction.guild
        await interaction.response.defer(ephemeral=False)

        reason = f"Banned due to grievances in discord.py: {self.target_reason!r}"
        await interaction.guild.ban(
            self.target,
            reason=shorten(reason, width=128, placeholder="..."),
        )
        await interaction.followup.send("Banned.")


class Moderation(commands.Cog):
    def __init__(self, bot: core.Bot, /) -> None:
        self.bot = bot
        self.dpy_mod_cache: dict[int, discord.User | discord.Member] = {}
        self._req_lock = asyncio.Lock()

    async def github_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> Any:
        api_key = core.CONFIG["TOKENS"].get("github_bot")
        if not api_key:
            return

        hdrs = {
            "Accept": "application/vnd.github.inertia-preview+json",
            "User-Agent": "PythonistaBot Moderation Cog",
            "Authorization": f"token {api_key}",
        }

        req_url = yarl.URL("https://api.github.com") / url

        if headers is not None:
            hdrs.update(headers)

        async with self._req_lock:
            async with self.bot.session.request(method, req_url, params=params, json=data, headers=hdrs) as r:
                remaining = r.headers.get("X-Ratelimit-Remaining")
                js = await r.json()

                if r.status == 429 or remaining == "0":
                    # wait before we release the lock
                    delta = discord.utils._parse_ratelimit_header(r)  # type: ignore # shh this is okay

                    await asyncio.sleep(delta)
                    self._req_lock.release()

                    return await self.github_request(method, url, params=params, data=data, headers=headers)

                elif 300 > r.status >= 200:
                    return js

                else:
                    raise GithubError(js["message"])

    async def create_gist(
        self,
        content: str,
        *,
        description: str | None = None,
        filename: str | None = None,
        public: bool = True,
    ) -> str:
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }

        filename = filename or "output.txt"
        data: dict[str, Any] = {
            "public": public,
            "files": {
                filename: {
                    "content": content,
                }
            },
        }

        if description:
            data["description"] = description

        js = await self.github_request("POST", "gists", data=data, headers=headers)
        return js["html_url"]

    @commands.Cog.listener("on_message")
    async def find_discord_tokens(self, message: discord.Message) -> None:
        tokens: list[str] = [token for token in TOKEN_RE.findall(message.content) if validate_token(token)]

        if not tokens:
            return

        url = await self.create_gist(
            "\n".join(tokens), filename="tokens.txt", description="Tokens found within the Pythonista guild."
        )

        msg: str = (
            f"Hey {message.author.mention}, I found one or more Discord Bot tokens in your message "
            f"and I've sent them off to be invalidated for you.\n"
            f"You can find the token(s) [here]({url})."
        )
        await message.reply(msg)

    @commands.Cog.listener()
    async def on_papi_dpy_modlog(self, payload: ModLogType, /) -> None:
        moderation_payload = payload["payload"]
        moderation_event = core.DiscordPyModerationEvent(moderation_payload["moderation_event_type"])

        embed = discord.Embed(
            title=f"Discord.py Moderation Event: {moderation_event.name.title()}",
            colour=random_pastel_colour(),
        )

        target_id = moderation_payload["target_id"]
        target = await self.bot.get_or_fetch_user(target_id)

        moderation_reason = moderation_payload["reason"]

        moderator_id = moderation_payload["author_id"]
        moderator = self.dpy_mod_cache.get(moderator_id) or await self.bot.get_or_fetch_user(
            moderator_id, cache=self.dpy_mod_cache
        )

        if moderator:
            self.dpy_mod_cache[moderator.id] = moderator
            moderator_format = f"{moderator.name} {PROSE_LOOKUP[moderation_event.value]} "
            embed.set_author(name=moderator.name, icon_url=moderator.display_avatar.url)
        else:
            moderator_format = f"Unknown Moderator with ID: {moderator_id} {PROSE_LOOKUP[moderation_event.value]} "
            embed.set_author(name=f"Unknown Moderator.")

        if target:
            target_format = target.name
            embed.set_footer(text=f"{target.name} | {target_id}", icon_url=target.display_avatar.url)
        else:
            target_format = f"An unknown user with ID {target_id}"
            embed.set_footer(text=f"Not Found | {target_id}")
        embed.add_field(name="Reason", value=moderation_reason or "No reason given.")

        embed.description = moderator_format + target_format

        when = datetime.datetime.fromisoformat(moderation_payload["event_time"])
        embed.timestamp = when

        guild = self.bot.get_guild(490948346773635102)
        assert guild

        channel = guild.get_channel(Channels.DPY_MOD_LOGS)
        assert isinstance(channel, discord.TextChannel)  # This is static

        view = ModerationRespostView(timeout=900, target_id=target_id, target_reason=moderation_reason)
        view.message = await channel.send(embed=embed, view=view)


async def setup(bot: core.Bot) -> None:
    await bot.add_cog(Moderation(bot))
