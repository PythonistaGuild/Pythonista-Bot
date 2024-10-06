from discord.enums import Enum

__all__ = ("DiscordPyModerationEvent",)


class DiscordPyModerationEvent(Enum):
    ban = 1
    kick = 2
    mute = 3
    unban = 4
    helpblock = 5
    generalblock = 6
    unmute = 7
    ungeneralblock = 8
    unhelpblock = 9
