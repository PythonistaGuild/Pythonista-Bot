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

import logging

from discord.ext import commands

import core
from core.errors import InvalidEval
from core.utils import formatters


LOGGER = logging.getLogger(__name__)


class Evaluation(core.Cog):
    """Evaluation Cog.

    The aim of this is to provide a safe, isolated and available environment for Pythonista's to run their code.
    """

    def __init__(self, bot: core.Bot, endpoint_url: str) -> None:
        self.bot = bot
        self.eval_endpoint: str = endpoint_url

    async def perform_eval(self, code: core.Codeblock) -> str:
        async with self.bot.session.post(self.eval_endpoint, json={"input": code.content[1]}) as eval_response:
            if eval_response.status != 200:
                raise InvalidEval(eval_response.status, "There was an issue running this eval command.")

            eval_data = await eval_response.json()

            return eval_data["stdout"]

    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def eval(
        self, ctx: core.Context, *, code: core.Codeblock = commands.param(converter=core.CodeblockConverter)
    ) -> None:
        """Evaluates your code in the form of a Discord message.

        Parameters
        ------------
        code_body: :class:`Codeblock`
            This will attempt to convert your current passed parameter into proper Python code.
        """
        reaction = "\U00002705"

        async with ctx.typing():
            try:
                output = await self.perform_eval(code)
            except InvalidEval:
                reaction = "\U0000274c"

                return await ctx.message.add_reaction(reaction)

            if len(output) > 1000:
                codeblock = await self.bot.mb_client.create_paste(content=output, filename="eval.py")

            else:
                codeblock = formatters.to_codeblock(output, escape_md=False)

            await ctx.message.add_reaction(reaction)
            await ctx.send(f"Hey {ctx.author.display_name}, here is your eval output:\n{codeblock}")

    @eval.error
    async def eval_error_handler(self, ctx: core.Context, error: commands.CommandError) -> None:
        """Eval command error handler."""
        error = getattr(error, "original", error)

        if isinstance(error, (commands.MaxConcurrencyReached, commands.CommandOnCooldown)):
            # let's silently suppress these error, don't want to spam the reaction / message delete
            return

        elif isinstance(error, core.InvalidEval):
            await ctx.send(f"Eval failed with status code: {error.error_code}.")


async def setup(bot: core.Bot) -> None:
    if key := core.CONFIG.get("SNEKBOX"):
        await bot.add_cog(Evaluation(bot, key["url"]))

    else:
        LOGGER.warning("Cannot load the Eval extension due to the SNEKBOX config not existing.")
