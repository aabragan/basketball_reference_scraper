import re
from datetime import datetime
from typing import Dict

import pandas as pd
from bs4 import BeautifulSoup
from requests import get
from unidecode import unidecode

try:
    from players import get_stats
    from request_utils import get_wrapper
    from utils import format_html, get_game_suffix, remove_accents
except:
    from basketball_reference_scraper.players import get_stats
    from basketball_reference_scraper.request_utils import get_wrapper
    from basketball_reference_scraper.utils import (format_html,
                                                    get_game_suffix,
                                                    remove_accents)


def get_box_scores(date, team1, team2, period="GAME", stat_type="BASIC"):
    """
    Get the box scores for a given game between two teams on a given date.

    Args:
        date (str): The date of the game in 'YYYY-MM-DD' format.
        team1 (str): The abbreviation of the first team.
        team2 (str): The abbreviation of the second team.
        period (str, optional): The period of the game to retrieve stats for. Defaults to 'GAME'.
        stat_type (str, optional): The type of stats to retrieve. Must be 'BASIC' or 'ADVANCED'. Defaults to 'BASIC'.

    Returns:
        dict: A dictionary containing the box scores for both teams.
    """
    if stat_type not in ["BASIC", "ADVANCED"]:
        raise ValueError('stat_type must be "BASIC" or "ADVANCED"')
    date = pd.to_datetime(date)
    suffix = get_game_suffix(date, team1, team2)
    url = f"https://www.basketball-reference.com/{suffix}"
    r = get_wrapper(url)

    if r.status_code == 200:
        dfs = []
        if period == "GAME":
            if stat_type == "ADVANCED":
                selectors = [f"box-{team1}-game-advanced", f"box-{team2}-game-advanced"]
            else:
                selectors = [f"box-{team1}-game-basic", f"box-{team2}-game-basic"]
        else:
            selectors = [
                f"box-{team1}-{period.lower()}-basic",
                f"box-{period.lower()}-game-basic",
            ]
        soup = BeautifulSoup(r.content, "html.parser")
        for selector in selectors:
            table = soup.find("table", {"id": selector})
            raw_df = pd.read_html(format_html(table))[0]
            df = _process_box(raw_df)
            if team1 in selector:
                df["PLAYER"] = df["PLAYER"].apply(
                    lambda name: remove_accents(name, team1, date.year)
                )
            if team2 in selector:
                df["PLAYER"] = df["PLAYER"].apply(
                    lambda name: remove_accents(name, team2, date.year)
                )
            dfs.append(df)
        return {team1: dfs[0], team2: dfs[1]}
    else:
        raise ConnectionError(f"Request to basketball reference failed for {url}")


def _process_box(df):
    """Perform basic processing on a box score - common to both methods

    Args:
        df (DataFrame): the raw box score df

    Returns:
        DataFrame: processed box score
    """
    df.columns = list(map(lambda x: x[1], list(df.columns)))
    df.rename(columns={"Starters": "PLAYER"}, inplace=True)
    if "Tm" in df:
        df.rename(columns={"Tm": "TEAM"}, inplace=True)
    reserve_index = df[df["PLAYER"] == "Reserves"].index[0]
    df = df.drop(reserve_index).reset_index().drop("index", axis=1)
    return df


def get_all_star_box_score(year: int):
    """Returns box star for all star game in a given year

    Args:
        year (int): the year of the all star game

    Raises:
        ValueError: if invalid year is intered
        ConnectionError: when server cannot be reached

    Returns:
        dict: dictionary containing entries (team name, box score dataframe) for each team
    """
    if year >= datetime.now().year or year < 1951:
        raise ValueError("Please enter a valid year")
    r = get_wrapper(f"https://www.basketball-reference.com/allstar/NBA_{year}.html")
    if r.status_code == 200:
        dfs = []
        soup = BeautifulSoup(r.content, "html.parser")
        team_names = list(
            map(lambda el: el.text, soup.select("div.section_heading > h2")[1:3])
        )
        for table in soup.find_all("table")[1:3]:
            raw_df = pd.read_html(format_html(table))[0]
            df = _process_box(raw_df)
            # drop team totals row (always last), totals row
            totals_index = df[df["MP"] == "Totals"].index[0]
            df = df.drop(totals_index).reset_index().drop("index", axis=1)
            df = df.drop(df.tail(1).index).reset_index().drop("index", axis=1)
            df["PLAYER"] = df["PLAYER"].apply(lambda x: unidecode(x))
            dfs.append(df)
        res: Dict[str, pd.DataFrame] = {team_names[0]: dfs[0], team_names[1]: dfs[1]}
        # add DNPs for all-star roster purposes
        # the all-star team each dnp is on is in parens. for some reasons this captures parens
        dnp_allstar_teams = re.findall(
            r"\((.*?)\)", soup.select("ul.page_index > li > div")[0].text
        )
        for i, dnp in enumerate(
            map(lambda el: el.text, soup.select("ul.page_index > li > div > a"))
        ):
            # check if the player is already in the dataframe because sometimes replacements are
            # listed twice (e.g. 1980)
            as_team = dnp_allstar_teams[i]
            if dnp not in res[as_team]["PLAYER"].values:
                # infer the added player's real team
                stats_df = get_stats(dnp, ask_matches=False)
                team = (
                    stats_df[stats_df["SEASON"] == f"{year-1}-{str(year)[-2:]}"]
                    .head(1)["TEAM"]
                    .values[0]
                )
                new_row = {"PLAYER": dnp, "TEAM": team}
                # set players allstar team from regexp
                df: pd.DataFrame = res[as_team]
                new_df: pd.DataFrame = pd.DataFrame([new_row])
                res[as_team] = pd.concat([df, new_df])
        return res
    else:
        raise ConnectionError("Request to basketball reference failed")
