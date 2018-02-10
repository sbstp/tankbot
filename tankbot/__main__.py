import json

import arrow
import praw
from attr import attrib, attrs

from .api import CachedInfo, Info, Team
from .generate import generate


@attrs
class Matchup:
    game = attrib()
    tanker = attrib(default=None)
    overtime = attrib(default=False)
    time = attrib(init=False)

    def __attrs_post_init__(self):
        self.time = self.game.time.format('HH:mm')

    @classmethod
    def from_game(cls, game, my_team):
        m = Matchup(game)
        my_standing = my_team.standing
        home_standing = game.home.standing
        away_standing = game.away.standing

        if game.home == my_team:
            m.tanker = game.away
        elif game.away == my_team:
            m.tanker = game.home
        elif home_standing.points <= my_standing.points and away_standing.points <= my_standing.points:
            m.overtime = True
        elif home_standing.points <= my_standing.points:
            m.tanker = game.home
        elif away_standing.points <= my_standing.points:
            m.tanker = game.away
        else:
            winner, _ = min([(game.home, home_standing), (game.away, away_standing)], key=lambda pair: pair[1].points)
            m.tanker = winner
        return m


def is_team_in_range(my_team, other):
    if my_team == other:
        return True
    return other.standing.points <= my_team.standing.points or abs(other.standing.points - my_team.standing.points) <= 5


def is_game_relevant(game, my_team: Team):
    return is_team_in_range(my_team, game.home) or is_team_in_range(my_team, game.away)


def compute_matchups(my_team: Team, games):
    my_matchup = False
    matchups = []

    for game in games:
        if not is_game_relevant(game, my_team):
            continue
        m = Matchup.from_game(game, my_team)

        if my_team == game.home or my_team == game.away:
            my_matchup = m
        else:
            matchups.append(m)

    return my_matchup, matchups


def test_salt():
    import random  # noqa
    pool = []
    pool.extend(range(ord('a'), ord('z') + 1))
    pool.extend(range(ord('A'), ord('Z') + 1))
    pool.extend(range(ord('0'), ord('9') + 1))
    return ''.join(chr(random.choice(pool)) for _ in range(5))


if __name__ == '__main__':
    with open('config.json') as f:
        config = json.load(f)
        test = config.get("test", False)

        info = CachedInfo() if test else Info()
        my_team = info.get_team_by_code(config['my_team'])
        my_matchup, matchups = compute_matchups(my_team, info.games)
        my_result, results = compute_matchups(my_team, info.results)
        standings = [s for s in info.standings if is_team_in_range(my_team, s.team)]
        text = generate(my_team, my_result, results, my_matchup, matchups, standings)

        if test:
            print(text)
        else:
            reddit = praw.Reddit(client_id=config['client_id'],
                                 client_secret=config['client_secret'],
                                 username=config['username'],
                                 password=config['password'],
                                 user_agent=config['user_agent'])

            sub = reddit.subreddit(config['subreddit'])
            sub.submit("Scouting the tank {} #{}".format(
                arrow.now().format('MMMM Do, YYYY'), test_salt()), selftext=text)