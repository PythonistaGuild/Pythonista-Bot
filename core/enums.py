from discord.enums import Enum

__all__ = ("DiscordPyModerationEvent",)


class DiscordPyModerationEvent(Enum):
    ban = 1
    kick = 2
    mute = 3
    unban = 4
    helpblock = 5
