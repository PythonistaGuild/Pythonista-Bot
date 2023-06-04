from __future__ import annotations

import asyncio
import base64
import binascii
import re
from typing import TYPE_CHECKING, Any

import discord
import yarl
from discord.ext import commands

import core


if TYPE_CHECKING:
    from bot import Bot

TOKEN_RE = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}")


def validate_token(token: str) -> bool:
    try:
        # Just check if the first part validates as a user ID
        (user_id, _, _) = token.split(".")
        user_id = int(base64.b64decode(user_id + "==", validate=True))
    except (ValueError, binascii.Error):
        return False
    else:
        return True


class GithubError(commands.CommandError):
    pass


class Moderation(commands.Cog):
    def __init__(self, bot: Bot, /) -> None:
        self.bot: Bot = bot
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
            "User-Agent": "RoboDanny DPYExclusive Cog",
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

        await message.reply(
            f"Hey {message.author.mention}, I found one or more Discord Bot tokens in your message and I've sent them off to be invalidated for you.\n"
            f"You can find the token(s) [here]({url})."
        )


async def setup(bot: Bot) -> None:
    await bot.add_cog(Moderation(bot))
