import re
from datetime import datetime
from typing import List

import pandas as pd
from bs4 import BeautifulSoup
from requests import get

from basketball_reference_scraper.teams import get_team_games

try:
    from request_utils import get_wrapper
except:
    from basketball_reference_scraper.request_utils import get_wrapper


def get_location(s):
    l = s.split(";")
    top = float(l[0][l[0].index(":") + 1 : l[0].index("px")])
    left = float(l[1][l[1].index(":") + 1 : l[1].index("px")])
    x = left / 500.0 * 50
    y = top / 472.0 * (94 / 2)
    return {"x": str(x)[:4] + " ft", "y": str(y)[:4] + " ft"}


def get_description(s):
    match = re.match(
        r"(\d)[a-z]{2} quarter, (\S*) remaining<br>(.*) \b(missed|made) (\d)-pointer from (\d*) ft",
        s,
    )
    d = {}
    if match:
        groups = match.groups()
        d["QUARTER"] = int(groups[0])
        d["TIME_REMAINING"] = groups[1]
        d["PLAYER"] = groups[2]
        d["MAKE_MISS"] = "MAKE" if groups[3] == "made" else "MISS"
        d["VALUE"] = int(groups[4])
        d["DISTANCE"] = groups[5] + " ft"
    return d


def get_shot_chart(date, team1, team2):
    date = pd.to_datetime(date)
    end_year = date.year + 1 if date.month > 9 else date.year
    team_games = get_team_games(team1, end_year, False)
    suffix = team_games[team_games["DATE"] == date.strftime("%Y-%m-%d")][
        "BOX_SCORE_LINK"
    ].iloc[0]
    suffix = suffix.replace("/boxscores", "")
    soup = get_wrapper(
        f"https://www.basketball-reference.com/boxscores/shot-chart{suffix}"
    )
    if soup:
        shot_chart1_div = soup.find("div", attrs={"id": f"shots-{team1}"})
        shot_chart2_div = soup.find("div", attrs={"id": f"shots-{team2}"})
        items1: List = []
        for div in shot_chart1_div.find_all("div"):
            if "style" not in div.attrs or "tip" not in div.attrs:
                continue
            location = get_location(div.attrs["style"])
            description = get_description(div.attrs["tip"])
            shot_d = {**location, **description}
            items1.append(shot_d)

        df1 = pd.DataFrame(items1)
        items2: List = []
        for div in shot_chart2_div.find_all("div"):
            if "style" not in div.attrs or "tip" not in div.attrs:
                continue
            location = get_location(div.attrs["style"])
            description = get_description(div.attrs["tip"])
            shot_d = {**location, **description}
            items2.append(shot_d)
        df2 = pd.DataFrame(items2)

        return {f"{team1}": df1, f"{team2}": df2}
    else:
        raise ConnectionError("Request to basketball reference failed")
