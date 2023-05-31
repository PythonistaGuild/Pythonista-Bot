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
from .meta import CONSTANTS

__all__ = ("Roles", "Colours", "League")


class Roles(CONSTANTS):
    # Human
    ADMIN: int = 490952483238313995
    MODERATOR: int = 578255729295884308
    KNOWLEDGEABLE: int = 490994825315745795
    PYTHONISTA_DEVELOPER: int = 763106310098911263
    HELPER: int = 649520971069390858
    CONTRIBUTOR: int = 763106223457304607
    MUTED: int = 491171912999763979
    NITRO_BOOSTER: int = 585638327009542170

    # Bots
    ADMIN_BOT: int = 490952487122108441
    GUILD_BOT: int = 570452583932493825
    TEST_BOT: int = 490954992384081930


class Colours(CONSTANTS):
    # Branding
    PYTHONISTA_BG: hex = 0x18344D
    PYTHON_YELLOW: hex = 0xFFDE57
    PYTHON_BLUE: hex = 0x4584B6


class League(CONSTANTS):
    # Endpoints
    API: str = "https://{region}.api.riotgames.com/{endpoint}/{query}"
    SUMMONER_BY_ID: str = "lol/summoner/v4/summoners"
    SUMMONER_BY_NAME: str = "lol/summoner/v4/summoners/by-name"
    RANKED_BY_SUMMONER_ID: str = "lol/league/v4/entries/by-summoner"
    MATCHES_BY_ACCOUNT_ID: str = "lol/match/v4/matchlists/by-account"
    MATCH_BY_ID: str = "lol/match/v4/matches"

    # Assets
    DD_VERSIONS_URL: str = "https://ddragon.leagueoflegends.com/api/versions.json"
    DD_CDN_URL: str = "https://ddragon.leagueoflegends.com/cdn/dragontail-{version}.tgz"
    DD_CHAMPIONS_URL: str = (
        "http://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    )

    # Regions
    BR: str = "br1"  # Brazil
    EUNE: str = "eun1"  # Europe Nordic and East
    EUW: str = "euw1"  # Europe West
    LAN: str = "la1"  # Latin America North
    LAS: str = "la2"  # Latin America South
    NA: str = "na1"  # North America
    OCE: str = "oc1"  # Oceanic
    RU: str = "ru"  # Russia
    TR: str = "tr1"  # Turkey
    JP: str = "jp1"  # Japan
    KR: str = "kr"  # Korea
