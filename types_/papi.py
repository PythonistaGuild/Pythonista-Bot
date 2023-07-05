from typing import Generic, Literal, TypedDict, TypeVar


PayloadT = TypeVar("PayloadT", bound=TypedDict)


class ModLogPayload(TypedDict):
    # event types:
    """
    1. Ban
    2. Kick
    3. Mute
    4. Unban
    5. Helpblock?
    """
    moderation_event_type: Literal[1, 2, 3, 4, 5]
    guild_id: int
    target_id: int
    author_id: int
    reason: str
    event_time: str  # isoformatted datetime


class PythonistaAPIWebsocketPayload(TypedDict, Generic[PayloadT]):
    op: int
    subscription: str
    application: int
    application_name: str
    payload: PayloadT
    user_id: int
