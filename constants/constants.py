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
from ._meta import CONSTANTS


__all__ = (
    "Roles",
    "Colours",
    "Channels",
    "ForumTags",
    "PAPIWebsocketSubscriptions",
    "PAPIWebsocketCloseCodes",
    "PAPIWebsocketNotificationTypes",
    "PAPIWebsocketOPCodes",
)


class Roles(CONSTANTS):
    # Human
    ADMIN: int = 490952483238313995
    MODERATOR: int = 578255729295884308
    MEMBERS: int = 1064477988013477939
    CHALLENGE_WINNER: int = 815949899853856788
    MUTED: int = 491171912999763979
    NITRO_BOOSTER: int = 585638327009542170

    # Bots
    ADMIN_BOT: int = 490952487122108441
    GUILD_BOT: int = 570452583932493825
    TEST_BOT: int = 490954992384081930


class Channels(CONSTANTS):
    HELP_FORUM = 1006716547223519293
    HELP_CHANNEL = 490951172673372195

    TWITCHIO_DEV = 669115391880069150
    WAVELINK_DEV = 739788459006492752
    MYSTBIN_DEV = 698366338774728714

    FORUM_LOGS = 1114743569786347550


class Colours(CONSTANTS):
    # Branding
    PYTHONISTA_BG: int = 0x18344D
    PYTHON_YELLOW: int = 0xFFDE57
    PYTHON_BLUE: int = 0x4584B6


class ForumTags(CONSTANTS):
    PYTHON = 1006716837041557574
    TWITCHIO = 1006716863469867060
    WAVELINK = 1006716892020473917
    DISCORDPY = 1006716972802789457
    OTHER = 1006717008613740596
    RESOLVED = 1006769269201195059


class PAPIWebsocketCloseCodes(CONSTANTS):
    NORMAL: int = 1000
    ABNORMAL: int = 1006


class PAPIWebsocketOPCodes(CONSTANTS):
    # Received from Pythonista API...
    HELLO: int = 0
    EVENT: int = 1
    NOTIFICATION: int = 2

    # Sent to Pythonista API...
    SUBSCRIBE: str = "subscribe"
    UNSUBSCRIBE: str = "unsubscribe"


class PAPIWebsocketSubscriptions(CONSTANTS):
    DPY_MOD_LOG: str = "discord_py_mod_log"


class PAPIWebsocketNotificationTypes(CONSTANTS):
    # Subscriptions...
    SUBSCRIPTION_ADDED: str = "subscription_added"
    SUBSCRIPTION_REMOVED: str = "subscription_removed"

    # Failures...
    UNKNOWN_OP: str = "unknown_op"
