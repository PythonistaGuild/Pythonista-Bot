# Pythonista-Bot

Primary Discord Bot for the Pythonista Guild!

## Setup Requirements

- [ ] Python 3.11+
- [ ] PostgreSQL 15+

You must make a valid copy of [the config file](./config.template.toml) named `config.toml`, fill in the blanks, and then...

### Optional
- [ ] Docker / Snekbox capability
This will allow for public evals. To disable the functionality entirely, ensure the `[SNEKBOX]` key is not present in the config file.


## Running the bot

In the future we'll provide a systemd unit, pm2 config and maybe a Dockerfile for running the bot, but for now you can use your ideal terminal and:-
```shell
python -O launcher.py
```

(we run with `python -O` because we use `assert` for type checking purposes).

### Docker

We also provide both `Dockerfile` and `docker-compose.yml` files for running the bot in Docker.
The default compose file assumes you want snekbox too, however you can comment out or remove that entire key if this is not the case.

Make a copy of `.template.env` and name it to `.env`, edit the values as you see fit (the defaults will work too, and be okay so long as you don't expose this database to the internet).
Then a simple `docker compose up` will bring your bot up!

(or `docker-compose` if you are not on the latest versions...)

#### Notes

This also means that it will use internal docker networking to resolve the database and snekbox names. By default these will be `database` and `snekbox`, but these will be the **service names** in `docker-compose.yml` if you change them. Please keep this in mind when editing your config file.

### Support

As this bot is not really designed for use outside of our Guild, support provided will be **very** limited.
But if you wish to chat to us, feel free to open a discussion, an issue or even a PR (for fixes and whatnot)!

Or chat to us on discord:-
<div align="left">
    <a href="https://discord.gg/RAKc3HF">
        <img src="https://discordapp.com/api/guilds/490948346773635102/widget.png?style=banner2" alt="Discord Server"/>
    </a>
</div>
