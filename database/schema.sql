CREATE TABLE IF NOT EXISTS starboard_entries (
    msg_id            BIGINT      PRIMARY KEY,
    bot_message_id    BIGINT,
    channel           BIGINT,
    stars             INT         NOT NULL DEFAULT 1,
    bot_content_id    BIGINT      NOT NULL
);

CREATE TABLE IF NOT EXISTS starers (
    user_id         BIGINT,
    msg_id          BIGINT
)