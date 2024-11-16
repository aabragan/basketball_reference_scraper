import re
from datetime import datetime
from typing import Dict

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    from request_utils import get_wrapper
    from utils import format_html
except:
    from basketball_reference_scraper.request_utils import get_wrapper
    from basketball_reference_scraper.utils import format_html


def get_schedule(season, playoffs=False):
    months = [
        "October",
        "November",
        "December",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
    ]
    if season == 2020:
        months = [
            "October-2019",
            "November",
            "December",
            "January",
            "February",
            "March",
            "July",
            "August",
            "September",
            "October-2020",
        ]
    df = pd.DataFrame()
    for month in months:
        r = get_wrapper(
            f"https://www.basketball-reference.com/leagues/NBA_{season}_games-{month.lower()}.html"
        )
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            table = soup.find("table", attrs={"id": "schedule"})
            if table:
                month_df = pd.read_html(format_html(table))[0]
                df = pd.concat([df, month_df])

    df = df.reset_index()

    cols_to_remove = [i for i in df.columns if "Unnamed: 6" in i]
    cols_to_remove += [i for i in df.columns if "Notes" in i]
    cols_to_remove += [i for i in df.columns if "Start" in i]
    cols_to_remove += [i for i in df.columns if "Attend" in i]
    cols_to_remove += [i for i in df.columns if "Arena" in i]
    cols_to_remove += ["index"]
    df = df.drop(cols_to_remove, axis=1)

    df.columns = ["DATE", "VISITOR", "VISITOR_PTS", "HOME", "HOME_PTS", "OT?", "LOG"]
    df["OT?"] = df["OT?"].fillna("N").apply(lambda x: "Y" if x == "OT" else "N")

    if season == 2020:
        df = df[df["DATE"] != "Playoffs"]
        df["DATE"] = df["DATE"].apply(lambda x: pd.to_datetime(x))
        df = df.sort_values(by="DATE")
        df = df.reset_index().drop("index", axis=1)
        playoff_loc = df[df["DATE"] == pd.to_datetime("2020-08-17")].head(n=1)
        if len(playoff_loc.index) > 0:
            playoff_index = playoff_loc.index[0]
        else:
            playoff_index = len(df)
        if playoffs:
            df = df[playoff_index:]
        else:
            df = df[:playoff_index]
    else:
        # account for 1953 season where there's more than one "playoffs" header
        if season == 1953:
            df.drop_duplicates(subset=["DATE", "HOME", "VISITOR"], inplace=True)
        playoff_loc = df[df["DATE"] == "Playoffs"]
        if len(playoff_loc.index) > 0:
            playoff_index = playoff_loc.index[0]
        else:
            playoff_index = len(df)
        if playoffs:
            df = df[playoff_index + 1 :]
        else:
            df = df[:playoff_index]
        df["DATE"] = df["DATE"].apply(lambda x: pd.to_datetime(x))
    return df


def get_standings(date=None):
    if date is None:
        date = datetime.now()
    else:
        date = pd.to_datetime(date)
    d = {}
    r = get_wrapper(
        f"https://www.basketball-reference.com/friv/standings.fcgi?month={date.month}&day={date.day}&year={date.year}"
    )
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        e_table = soup.find("table", attrs={"id": "standings_e"})
        e_teams = e_table.find_all("a", href=re.compile("/teams/"))
        team_map: Dict[str, str] = {}
        for e_team in e_teams:
            key = str(e_team.next)
            value = (
                str(e_team["href"])
                .replace(".html", "")
                .replace("/teams/", "")
                .split("/")[0]
            )
            team_map[key] = value

        w_table = soup.find("table", attrs={"id": "standings_w"})
        w_teams = w_table.find_all("a", href=re.compile("/teams/"))
        for w_team in w_teams:
            key = str(w_team.next)
            value = (
                str(w_team["href"])
                .replace(".html", "")
                .replace("/teams/", "")
                .split("/")[0]
            )
            team_map[key] = value

        e_df = pd.DataFrame(
            columns=["TEAM", "W", "L", "W/L%", "GB", "PW", "PL", "PS/G", "PA/G"]
        )
        w_df = pd.DataFrame(
            columns=["TEAM", "W", "L", "W/L%", "GB", "PW", "PL", "PS/G", "PA/G"]
        )

        if e_table and w_table:
            e_df = pd.read_html(format_html(e_table))[0]
            w_df = pd.read_html(format_html(w_table))[0]
            e_df.rename(columns={"Eastern Conference": "TEAM"}, inplace=True)
            w_df.rename(columns={"Western Conference": "TEAM"}, inplace=True)

        e_df["ABBREV"] = e_df["TEAM"].map(team_map)
        w_df["ABBREV"] = w_df["TEAM"].map(team_map)
        d["EASTERN_CONF"] = e_df
        d["WESTERN_CONF"] = w_df
        return d
    else:
        raise ConnectionError("Request to basketball reference failed")


def get_advanced_team_stats(season_end_year):
    url = f"https://www.basketball-reference.com/leagues/NBA_{season_end_year}.html"

    response = requests.get(url)

    content = BeautifulSoup(response.content, "html.parser")
    table = content.find("table", {"id": "advanced-team"})

    teams = table.find_all("a", href=re.compile("/teams/"))
    team_map: Dict[str, str] = {}
    for team in teams:
        key = str(team.next)
        value = (
        str(team["href"])
        .replace(".html", "")
        .replace("/teams/", "")
        .split("/")[0]
        )
        team_map[key] = value

    df = pd.read_html(format_html(table))[0]
    df.columns = df.columns.map("|".join)
    df.rename(columns=lambda c: c.split("|")[1], inplace=True)
    df.drop(
        columns=["Unnamed: 17_level_1", "Unnamed: 22_level_1", "Unnamed: 27_level_1"],
        inplace=True,
    )

    df = df.iloc[:, :-3]
    df.drop(df.tail(1).index, inplace=True)
    df.columns = [
        "RANK",
        "TEAM",
        "AGE",
        "WIN",
        "LOSS",
        "PYTH_WIN",
        "PYTH_LOSS",
        "MOV",
        "SOS",
        "SRS",
        "ORTG",
        "DRTG",
        "NRTG",
        "PACE",
        "FTAR",
        "3PAR",
        "TS_P",
        "O_EFG_P",
        "O_TOV_P",
        "O_ORB_P",
        "O_FT_FGA",
        "D_EFG_P",
        "D_TOV_P",
        "D_DRB_P",
        "D_FT_FGA",
    ]
    df["ABBREV"] = df["TEAM"].map(team_map)
    return df
