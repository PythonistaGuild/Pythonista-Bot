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
import logging
import re
from typing import Any

import discord
import yarl
from discord.ext import commands

import core


logger = logging.getLogger(__name__)

TOKEN_RE = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}")
BASE_BADBIN_RE = r"https://(?P<site>{domains})/(?P<slug>[a-zA-Z0-9]+)[.]?(?P<ext>[a-z]{{1,8}})?"


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
    def __init__(self, bot: core.Bot, /) -> None:
        self.bot = bot
        self._req_lock = asyncio.Lock()

        domains = core.CONFIG["BADBIN"]["domains"]
        formatted = BASE_BADBIN_RE.format(domains="|".join(domains))

        self.BADBIN_RE = re.compile(formatted)
        logger.info("Badbin initialized with following domains: %s", ", ".join(domains))

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

        msg: str = (
            f"Hey {message.author.mention}, I found one or more Discord Bot tokens in your message "
            f"and I've sent them off to be invalidated for you.\n"
            f"You can find the token(s) [here]({url})."
        )
        await message.reply(msg)

    async def pull_badbin_content(self, site: str, slug: str, *, fail_hard: bool = True) -> str:
        async with self.bot.session.get(f"https://{site}/raw/{slug}") as f:
            if 200 > f.status > 299:
                if fail_hard:
                    f.raise_for_status()
                else:
                    err = f"Could not read {slug} from {site}. Details: {f.status}\n\n{await f.read()}"
                    logger.error(err)
                    return err  # if we don't fail hard, we'll return the error message in the new paste.

            return (await f.read()).decode()

    async def post_mystbin_content(self, contents: list[tuple[str, str]]) -> tuple[str, str | None]:
        hdrs = {}
        if core.CONFIG["TOKENS"]["mystbin"]:
            hdrs["Authorization"] = core.CONFIG["TOKENS"]["mystbin"]

        async with self.bot.session.put(
            "https://api.mystb.in/paste",
            headers=hdrs,
            json={"files": [{"filename": x[1], "content": x[0]} for x in contents]},
        ) as resp:
            if 200 > resp.status > 299:
                resp.raise_for_status()

            data = await resp.json()
            return data["id"], data.get("notice") or None

    @commands.Cog.listener("on_message")
    async def find_badbins(self, message: discord.Message) -> None:
        matches = self.BADBIN_RE.findall(message.content)

        if matches:
            contents: list[tuple[str, str]] = []

            for match in matches:
                site, slug, ext = match

                if site is None or slug is None:
                    continue

                contents.append((await self.pull_badbin_content(site, slug), f"migrated.{ext or 'txt'}"))

            if contents:
                key, notice = await self.post_mystbin_content(contents)
                msg = f"I've detected a badbin and have uploaded your pastes here: https://mystb.in/{key}"

                if notice:
                    msg += "\nnotice: " + notice

                await message.reply(msg, mention_author=False)


async def setup(bot: core.Bot) -> None:
    await bot.add_cog(Moderation(bot))
