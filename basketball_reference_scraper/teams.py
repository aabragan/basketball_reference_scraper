import re

import pandas as pd
from bs4 import BeautifulSoup

try:
    from constants import TEAM_SETS, TEAM_TO_TEAM_ABBR
    from request_utils import get_selenium_wrapper, get_wrapper
    from utils import format_html, remove_accents
except:
    from basketball_reference_scraper.constants import (TEAM_SETS,
                                                        TEAM_TO_TEAM_ABBR)
    from basketball_reference_scraper.request_utils import (
        get_selenium_wrapper, get_wrapper)
    from basketball_reference_scraper.utils import format_html, remove_accents


def get_roster(team, season_end_year):
    r = get_wrapper(
        f"https://www.basketball-reference.com/teams/{team}/{season_end_year}.html"
    )
    df = None
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        table = soup.find("table", {"id": "roster"})
        # get all player page urls
        player_links = table.find_all("a", href=re.compile("/players/"))
        player_id_map = {}
        # build lookup of player ids
        for item in player_links:
            key = str(item.next)
            value = str(item["href"]).replace(".html", "").replace("/players/", "")[2:]
            player_id_map[key] = value

        df = pd.read_html(format_html(table))[0]
        df.columns = [
            "NUMBER",
            "PLAYER",
            "POS",
            "HEIGHT",
            "WEIGHT",
            "BIRTH_DATE",
            "NATIONALITY",
            "EXPERIENCE",
            "COLLEGE",
        ]

        # remove (TW) suffix from player name
        df["PLAYER"] = df["PLAYER"].apply(lambda x: str(x).replace("(TW)", "").strip())
        # map player id using player name
        df["PLAYER_ID"] = df["PLAYER"].map(player_id_map)

        # remove rows with no player name (this was the issue above)
        df = df[df["PLAYER"].notna()]
        df["PLAYER"] = df["PLAYER"].apply(
            lambda name: remove_accents(name, team, season_end_year)
        )
        # handle rows with empty fields but with a player name.
        df["BIRTH_DATE"] = df["BIRTH_DATE"].apply(
            lambda x: pd.to_datetime(x) if pd.notna(x) else pd.NaT
        )
        df["NATIONALITY"] = df["NATIONALITY"].apply(
            lambda x: x.upper() if pd.notna(x) else ""
        )

    return df


def get_team_stats(team, season_end_year, data_format="TOTALS"):
    xpath = '//table[@id="team_and_opponent"]'
    table = get_selenium_wrapper(
        f"https://www.basketball-reference.com/teams/{team}/{season_end_year}.html",
        xpath,
    )
    if not table:
        raise ConnectionError("Request to basketball reference failed")
    df = pd.read_html(format_html(table))[0]
    opp_idx = df[df["Unnamed: 0"] == "Opponent"].index[0]
    df = df[:opp_idx]
    if data_format == "TOTALS":
        row_idx = "Team"
    elif data_format == "PER_GAME":
        row_idx = "Team/G"
    elif data_format == "RANK":
        row_idx = "Lg Rank"
    elif data_format == "YEAR/YEAR":
        row_idx = "Year/Year"
    else:
        print("Invalid data format")
        return pd.DataFrame()

    s = df[df["Unnamed: 0"] == row_idx]
    s = s.drop(columns=["Unnamed: 0"]).reindex()
    return pd.Series(index=list(s.columns), data=s.values.tolist()[0])


def get_opp_stats(team, season_end_year, data_format="PER_GAME"):
    xpath = '//table[@id="team_and_opponent"]'
    table = get_selenium_wrapper(
        f"https://www.basketball-reference.com/teams/{team}/{season_end_year}.html",
        xpath,
    )
    if not table:
        raise ConnectionError("Request to basketball reference failed")
    df = pd.read_html(format_html(table))[0]
    opp_idx = df[df["Unnamed: 0"] == "Opponent"].index[0]
    df = df[opp_idx:]
    if data_format == "TOTALS":
        row_idx = "Opponent"
    elif data_format == "PER_GAME":
        row_idx = "Opponent/G"
    elif data_format == "RANK":
        row_idx = "Lg Rank"
    elif data_format == "YEAR/YEAR":
        row_idx = "Year/Year"
    else:
        print("Invalid data format")
        return pd.DataFrame()

    s = df[df["Unnamed: 0"] == row_idx]
    s = s.drop(columns=["Unnamed: 0"]).reindex()
    return pd.Series(index=list(s.columns), data=s.values.tolist()[0])


def get_team_misc(team, season_end_year, data_format="TOTALS"):
    xpath = '//table[@id="team_misc"]'
    table = get_selenium_wrapper(
        f"https://www.basketball-reference.com/teams/{team}/{season_end_year}.html",
        xpath,
    )
    if not table:
        raise ConnectionError("Request to basketball reference failed")
    df = pd.read_html(format_html(table))[0]
    if data_format == "TOTALS":
        row_idx = "Team"
    elif data_format == "RANK":
        row_idx = "Lg Rank"
    else:
        print("Invalid data format")
        return pd.DataFrame()
    df.columns = df.columns.droplevel()
    df.rename(columns={"Arena": "ARENA", "Attendance": "ATTENDANCE"}, inplace=True)
    s = df[df["Unnamed: 0_level_1"] == row_idx]
    s = s.drop(columns=["Unnamed: 0_level_1"]).reindex()
    return pd.Series(index=list(s.columns), data=s.values.tolist()[0])


def get_roster_stats(
    team: str, season_end_year: int, data_format="PER_GAME", playoffs=False
):
    if playoffs:
        xpath = f'//table[@id="playoffs_{data_format.lower()}"]'
    else:
        xpath = f'//table[@id="{data_format.lower()}"]'
    table = get_selenium_wrapper(
        f"https://www.basketball-reference.com/teams/{team}/{season_end_year}.html",
        xpath,
    )
    if not table:
        raise ConnectionError("Request to basketball reference failed")

    # get all player page urls
    soup = BeautifulSoup(table, "html.parser")
    # roster_table = soup.find("table", {"id": f"{data_format.lower()}"})
    player_links = soup.find_all("a", href=re.compile("/players/"))
    player_id_map = {}
    # build lookup of player ids
    for item in player_links:
        href = str(item["href"])
        if "/gamelog/" in href:
            continue
        key = str(item.next)
        value = str(item["href"]).replace(".html", "").replace("/players/", "")[2:]
        player_id_map[key] = value

    df = pd.read_html(format_html(table))[0]
    df.rename(
        columns={"Player": "PLAYER", "Age": "AGE", "Tm": "TEAM", "Pos": "POS"},
        inplace=True,
    )
    # remove (TW) suffix from player name
    df["PLAYER"] = df["PLAYER"].apply(lambda x: str(x).replace("(TW)", "").strip())

    # map player id using player name
    df["PLAYER_ID"] = df["PLAYER"].map(player_id_map)

    df["PLAYER"] = df["PLAYER"].apply(
        lambda name: remove_accents(name, team, season_end_year)
    )

    df = df.reset_index().drop(["Rk", "index"], axis=1)
    return df


def get_team_ratings(season_end_year: int, team=[]):
    r = get_wrapper(
        f"https://www.basketball-reference.com/leagues/NBA_{season_end_year}_ratings.html"
    )
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        table = soup.find("table", {"id": "ratings"})

        df = pd.read_html(format_html(table))[0]
        # Clean columns and indexes
        df = df.droplevel(level=0, axis=1)

        upper_cols = list(pd.Series(df.columns).apply(lambda x: x.upper()))
        df.columns = upper_cols
        df.dropna(inplace=True)
        df = df[df["RK"] != "Rk"]
        df["TEAM"] = df["TEAM"].apply(lambda x: x.upper())
        df["TEAM"] = df["TEAM"].apply(lambda x: TEAM_TO_TEAM_ABBR[x])

        # Add 'Season' column in and change order of columns
        df["SEASON"] = f"{season_end_year-1}-{str(season_end_year)[2:]}"
        cols = df.columns.tolist()
        cols = cols[0:1] + cols[-1:] + cols[1:-1]
        df = df[cols]

        # Add the ability to either pass no teams (empty list), one team (str), or multiple teams (list)
        if len(team) > 0:
            if isinstance(team, str):
                list_team = []
                list_team.append(team)
                df = df[df["TEAM"].isin(list_team)]
            else:
                df = df[df["TEAM"].isin(team)]
        df = df.reindex()
        return df
    else:
        raise ConnectionError("Request to basketball reference failed")


def get_teams(season_end_year):
    r = get_wrapper(
        f"https://www.basketball-reference.com/leagues/NBA_{season_end_year}.html"
    )
    df = None
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")

        east_conf_table = soup.find("table", {"id": "confs_standings_E"})
        east_df = pd.read_html(format_html(east_conf_table))[0]
        east_df.columns = [
            "TEAM_NAME",
            "WINS",
            "LOSSES",
            "WIN_LOSS_PCT",
            "GB",
            "PTS_PER_G",
            "OPP_PTS_PER_G",
            "SRS",
        ]

        west_conf_table = soup.find("table", {"id": "confs_standings_W"})
        west_df = pd.read_html(format_html(west_conf_table))[0]
        west_df.columns = [
            "TEAM_NAME",
            "WINS",
            "LOSSES",
            "WIN_LOSS_PCT",
            "GB",
            "PTS_PER_G",
            "OPP_PTS_PER_G",
            "SRS",
        ]

        df = pd.concat([east_df, west_df])

    return df
