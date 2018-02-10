# Is this a good idea? Probably not.


def _make_odds_func(info):
    with open('data/lottery') as f:
        odds = list(map(float, f.read().splitlines()))

    def func(s):
        try:
            return odds[len(info.teams) - s.place]
        except IndexError:
            return 0

    return func


def _underline_header(header):
    return "|".join([":---:"] * len(header.split('|')))


def _get_mood(my_team, r):
    # if should have went to overtime and it did, perfect
    if r.overtime and r.game.overtime:
        return "Perfect"
    # if the enemy tanker won
    elif r.tanker == r.game.winner:
        return "Yes"
    # if the enemy tanker didn't win but went to OT
    elif r.game.overtime and r.game.winner != my_team:
        return "Half yay"
    # no win, no OT
    else:
        return "No"


def _get_team(t):
    return '[](/r/{}) {}'.format(t.subreddit, t.code.upper())


def _generate_result_line(my_team, r):
    yield "{} at {}|{}-{} {} {}|{}".format(
        _get_team(r.game.away),
        _get_team(r.game.home),
        r.game.away_score,
        r.game.home_score,
        _get_team(r.game.winner),
        "(OT)" if r.game.overtime else "",
        _get_mood(my_team, r),
    )


def _generate_game_line(my_team, r):
    yield "{} at {}|{}|{}".format(
        _get_team(r.game.away),
        _get_team(r.game.home),
        "Overtime" if r.overtime else _get_team(r.tanker),
        r.time,
    )


def _generate_standings(standings, odds):
    header = "Place|Team|GP|Record|Points|ROW|Projection|1st pick odds"
    header_lines = _underline_header(header)
    yield "## Standings"
    yield ""
    yield header
    yield header_lines
    for s in standings:
        yield "{}|{}|{}|{}|{}|{}|{}|{:0.1f}".format(
            s.place,
            _get_team(s.team),
            s.gamesPlayed,
            "{:02}-{:02}-{:02}".format(s.wins, s.losses, s.ot),
            s.points,
            s.row,
            s.projection,
            odds(s),
        )
    yield ""
    yield "[Lottery odds, as well as a Lottery Simulator can be found here.](http://nhllotterysimulator.com)"
    yield ""


def _generate_tank_section(my_team, my, lst, title, header, func):
    header_lines = _underline_header(header)
    yield "## {}".format(title)
    yield ""
    yield "- De Tanque:"
    yield ""
    if my:
        yield header
        yield header_lines
        yield from func(my_team, my)
    else:
        yield "Nothing."
    yield ""
    yield "- Out of town tank:"
    yield ""
    if len(lst) > 0:
        yield header
        yield header_lines
        for entry in lst:
            yield from func(my_team, entry)
    else:
        yield "Nothing out of town."
    yield ""


def _generate(info, my_team, my_result, results, my_game, games, standings):
    odds = _make_odds_func(info)
    yield "# Scouting the Tank"
    yield from _generate_tank_section(my_team, my_result, results,
                                      "Last night's tank", "Game|Score|Yay?", _generate_result_line)
    yield "---"
    yield from _generate_standings(standings, odds)
    yield "---"
    yield from _generate_tank_section(my_team, my_game, games,
                                      "Tonight's tank", "Game|Cheer for?|Time", _generate_game_line)
    yield "---"
    yield "I'm a robot. My source is available [here](https://github.com/sbstp/tankbot)."


def generate(*args):
    return '\n'.join(_generate(*args))
