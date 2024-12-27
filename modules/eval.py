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

import ast
import logging
import textwrap
import traceback

import mystbin
from discord.ext import commands

import core
from core.errors import InvalidEval
from core.utils import formatters

LOGGER = logging.getLogger(__name__)


CODE = """
def __user_code__():
{user_code}

__value__ = __user_code__()
if __value__:
    print(__value__)
"""


class Evaluation(core.Cog):
    """Evaluation Cog.

    The aim of this is to provide a safe, isolated and available environment for Pythonista's to run their code.
    """

    def __init__(self, bot: core.Bot, endpoint_url: str) -> None:
        self.bot = bot
        self.eval_endpoint: str = endpoint_url

    async def perform_eval(self, code: core.Codeblock) -> str:
        source = code.content

        try:
            parsed = ast.parse(source, filename="<input>")
        except SyntaxError as e:
            return "".join(traceback.format_exception(type(e), e, e.__traceback__))

        if isinstance(parsed.body[-1], ast.Expr):
            expr: ast.Expr = parsed.body[-1]

            lineno = expr.lineno - 1

            co_mangled = source.splitlines()
            co_mangled[lineno] = "return " + co_mangled[lineno]

            source = "\n".join(co_mangled)

        formatted = CODE.format(user_code=textwrap.indent(source.replace("\t", "    "), "    "))

        async with self.bot.session.post(self.eval_endpoint, json={"input": formatted}) as eval_response:
            if eval_response.status != 200:
                response_text = await eval_response.text()
                raise InvalidEval(eval_response.status, response_text)

            eval_data = await eval_response.json()

            return eval_data["stdout"]

    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def eval(
        self,
        ctx: core.Context,
        *,
        code: core.Codeblock = commands.param(converter=core.CodeblockConverter),  # noqa: B008 # this is how converters work
    ) -> None:
        """Evaluates your code in the form of a Discord message.

        Parameters
        ------------
        code_body: :class:`Codeblock`
            This will attempt to convert your current passed parameter into proper Python code.
        """

        async with ctx.typing():
            output = await self.perform_eval(code)
            await ctx.message.add_reaction("\U00002705")

            if len(output) > 1000:
                try:
                    codeblock = await self.bot.mb_client.create_paste(
                        files=[mystbin.File(content=output, filename="eval.py")],
                    )
                except mystbin.APIException:
                    await ctx.send("Your output was too long to provide in any sensible manner.")
                    return

            elif output:
                codeblock = formatters.to_codeblock(output, escape_md=False)

            else:
                await ctx.send(f"Hey {ctx.author.display_name}, your code ran successfully, and returned nothing")
                return

            await ctx.send(f"Hey {ctx.author.display_name}, here is your eval output:\n{codeblock}")

    @eval.error
    async def eval_error_handler(self, ctx: core.Context, error: commands.CommandError) -> None:
        """Eval command error handler."""
        error = getattr(error, "original", error)

        if isinstance(error, (commands.MaxConcurrencyReached, commands.CommandOnCooldown)):
            # let's silently suppress these error, don't want to spam the reaction / message delete
            return

        if isinstance(error, core.InvalidEval):
            await ctx.send(
                f"Hey! Your eval job failed with status code: {error.error_code}. "
                f"Error message is below:-\n{error}.\nDon't worry, the team here know!",
            )
            LOGGER.error("Eval Cog raised an error during eval:\n%s", str(error))


async def setup(bot: core.Bot) -> None:
    if key := core.CONFIG.get("SNEKBOX"):
        await bot.add_cog(Evaluation(bot, key["url"]))

    else:
        LOGGER.warning("Cannot load the Eval extension due to the SNEKBOX config not existing.")
