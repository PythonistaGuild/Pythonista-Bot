"""MIT License

Copyright (c) 2020 PythonistaGuild

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
import enum
from typing import List, Optional, Union


__all__ = ('LeagueQueueType',
           'LeagueSeries',
           'LeagueSummoner',
           'LeagueSummonerRanked')


RANK_VALUES = {'IRON': 0,
               'BRONZE': 10,
               'SILVER': 20,
               'GOLD': 30,
               'PLATINUM': 40,
               'DIAMOND': 50,
               'MASTER': 60,
               'GRANDMASTER': 70,
               'CHALLENGER': 100,
               1: 3,
               2: 2,
               3: 1,
               4: 0}


class LeagueQueueType(enum.Enum):

    unranked = 0
    flex = 1
    solo = 2


class LeagueSeries:

    __slots__ = ('target',
                 'wins',
                 'losses',
                 'progress')

    def __init__(self, *, payload: dict):
        self.target: int = payload.get('target')
        self.wins: int = payload.get('wins')
        self.losses: int = payload.get('losses')

        bool_mapping = {'W': True, 'L': False, 'N': None}
        self.progress: List[Union[bool, None]] = [bool_mapping[m] for m in payload.get('progress')]


class LeagueSummoner:

    __slots__ = ('summoner_id',
                 'name',
                 'icon_id',
                 'level')

    def __init__(self, *, payload: dict):
        self.summoner_id: str = payload.get('id')
        self.name: str = payload.get('name')
        self.icon_id: int = payload.get('profileIconId')
        self.level: int = payload.get('summonerLevel')


class LeagueSummonerRanked:

    __slots__ = ('solo_tier',
                 'solo_rank',
                 'solo_points',
                 'solo_wins',
                 'solo_losses',
                 'solo_veteran',
                 'solo_inactive',
                 'solo_fresh',
                 'solo_streak',
                 'solo_series',
                 'solo_rate',
                 'flex_tier',
                 'flex_rank',
                 'flex_points',
                 'flex_wins',
                 'flex_losses',
                 'flex_veteran',
                 'flex_inactive',
                 'flex_fresh',
                 'flex_streak',
                 'flex_series',
                 'flex_rate')

    def __init__(self, *, payload: dict):
        for queue in payload:
            if queue['queueType'] == 'RANKED_SOLO_5x5':

                self.solo_tier: Optional[str] = queue.get('tier')
                self.solo_rank: Optional[int] = len(queue.get('rank'))
                self.solo_points: Optional[int] = queue.get('leaguePoints')
                self.solo_wins: Optional[int] = queue.get('wins')
                self.solo_losses: Optional[int] = queue.get('losses')
                self.solo_veteran: Optional[bool] = queue.get('veteran')
                self.solo_inactive: Optional[bool] = queue.get('inactive')
                self.solo_fresh: Optional[bool] = queue.get('freshBlood')
                self.solo_streak: Optional[bool] = queue.get('hotStreak')
                self.solo_series: Optional[LeagueSeries] = LeagueSeries(payload=queue.get('miniSeries'))
                self.solo_rate: Optional[float] = (self.solo_wins / (self.solo_wins + self.solo_losses)) * 100

            elif queue['queueType'] == 'RANKED_FLEX_SR':

                self.flex_tier: Optional[str] = queue.get('tier')
                self.flex_rank: Optional[int] = len(queue.get('rank'))
                self.flex_points: Optional[int] = queue.get('leaguePoints')
                self.flex_wins: Optional[int] = queue.get('wins')
                self.flex_losses: Optional[int] = queue.get('losses')
                self.flex_veteran: Optional[bool] = queue.get('veteran')
                self.flex_inactive: Optional[bool] = queue.get('inactive')
                self.flex_fresh: Optional[bool] = queue.get('freshBlood')
                self.flex_streak: Optional[bool] = queue.get('hotStreak')
                self.flex_series: Optional[LeagueSeries] = LeagueSeries(payload=queue.get('miniSeries'))
                self.flex_rate: Optional[float] = (self.flex_wins / (self.flex_wins + self.flex_losses)) * 100

    def __getattr__(self, item: str) -> None:
        if item in self.__slots__:
            return None

        raise AttributeError(f'{self.__class__.__name__} has no attribute <{item}>.')

    @property
    def top_queue(self) -> Optional[LeagueQueueType]:
        if self.solo_tier and not self.flex_tier:
            return LeagueQueueType.solo
        elif self.flex_tier and not self.solo_tier:
            return LeagueQueueType.flex
        elif not self.solo_tier and not self.flex_tier:
            return LeagueQueueType.unranked

        solo_pos: int = RANK_VALUES[self.solo_tier] + RANK_VALUES[self.solo_rank]
        flex_pos: int = RANK_VALUES[self.flex_tier] + RANK_VALUES[self.flex_rank]

        if solo_pos > flex_pos:
            return LeagueQueueType.solo
        elif flex_pos > solo_pos:
            return LeagueQueueType.flex

        if self.solo_points > self.flex_points:
            return LeagueQueueType.solo
        elif self.flex_points > self.solo_points:
            return LeagueQueueType.flex

        return None
