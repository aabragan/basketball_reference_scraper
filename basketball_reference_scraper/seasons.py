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

import random
import time


def get_schedule(season, playoffs=False):
    months = [
        "October",
        "November",
        "December",
        "January",
        "February",
        "March",
        "April",
    ]
    if playoffs:
        months.extend(["May", "June"])

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
    df = None
    game_rows = []
    for month in months:
        soup = get_wrapper(
            f"https://www.basketball-reference.com/leagues/NBA_{season}_games-{month.lower()}.html"
        )
        if soup:
            table = soup.find("table", {"id": "schedule"})
            if table is None:
                continue
            table_body = table.find_all("tbody")
            rows = table_body[0].find_all("tr")
            for row in rows:
                if row.get("class") is not None:
                    continue
                date_col = row.find("th", {"data-stat": "date_game"})
                if date_col is None:
                    continue
                game_date_str = date_col.get("csk")[:-4]
                game_date = datetime.strptime(game_date_str, "%Y%m%d")

                visitor_abbrev = ""
                visitor_name = ""
                visitor_pts = ""
                home_abbrev = ""
                home_name = ""
                home_pts = ""
                box_score_url = ""
                overtime = ""
                duration = ""

                cols = row.find_all("td")
                for col in cols:
                    if col.get("data-stat") is not None:
                        if col.get("data-stat") == "visitor_team_name":
                            visitor_abbrev = col.get("csk")[:3]
                            visitor_name = col.next.get_text()
                        elif col.get("data-stat") == "visitor_pts":
                            visitor_pts = col.get_text()
                        elif col.get("data-stat") == "home_team_name":
                            home_abbrev = col.get("csk")[:3]
                            home_name = col.next.get_text()
                        elif col.get("data-stat") == "home_pts":
                            home_pts = col.get_text()
                        elif col.get("data-stat") == "box_score_text":
                            box_score_url = col.next.get("href")
                        elif col.get("data-stat") == "overtimes":
                            overtime = "Y" if col.get_text() == "OT" else "N"
                        elif col.get("data-stat") == "game_duration":
                            duration = col.get_text()

                df_row = [
                    game_date,
                    visitor_abbrev,
                    visitor_name,
                    visitor_pts,
                    home_abbrev,
                    home_name,
                    home_pts,
                    box_score_url,
                    overtime,
                    duration,
                ]
                game_rows.append(df_row)

            df = pd.DataFrame(
                game_rows,
                columns=[
                    "DATE",
                    "VISITOR_ABBREV",
                    "VISITOR",
                    "VISITOR_PTS",
                    "HOME_ABBREV",
                    "HOME",
                    "HOME_PTS",
                    "BOX_SCORE_LINK",
                    "OT",
                    "DURATION",
                ],
            )

            # month_df = pd.read_html(format_html(table))[0]
            # df = pd.concat([df, month_df])

    # df = df.reset_index()

    # cols_to_remove = [i for i in df.columns if "Unnamed: 6" in i]
    # cols_to_remove += [i for i in df.columns if "Notes" in i]
    # cols_to_remove += [i for i in df.columns if "Start" in i]
    # cols_to_remove += [i for i in df.columns if "Attend" in i]
    # cols_to_remove += [i for i in df.columns if "Arena" in i]
    # cols_to_remove += ["index"]
    # df = df.drop(cols_to_remove, axis=1)

    # df.columns = ["DATE", "VISITOR", "VISITOR_PTS", "HOME", "HOME_PTS", "OT?", "LOG"]
    # df["OT?"] = df["OT?"].fillna("N").apply(lambda x: "Y" if x == "OT" else "N")
    # df = df[~df["DATE"].isin(["Date"])]

    # if season == 2020:
    #     df = df[df["DATE"] != "Playoffs"]
    #     df["DATE"] = pd.to_datetime(df["DATE"])
    #     df = df.sort_values(by="DATE")
    #     df = df.reset_index().drop("index", axis=1)
    #     playoff_loc = df[df["DATE"] == pd.to_datetime("2020-08-17")].head(n=1)
    #     if len(playoff_loc.index) > 0:
    #         playoff_index = playoff_loc.index[0]
    #     else:
    #         playoff_index = len(df)
    #     if playoffs:
    #         df = df[playoff_index:]
    #     else:
    #         df = df[:playoff_index]
    # else:
    #     # account for 1953 season where there's more than one "playoffs" header
    #     if season == 1953:
    #         df.drop_duplicates(subset=["DATE", "HOME", "VISITOR"], inplace=True)
    #     playoff_loc = df[df["DATE"] == "Playoffs"]
    #     if len(playoff_loc.index) > 0:
    #         playoff_index = playoff_loc.index[0]
    #     else:
    #         playoff_index = len(df)
    #     if playoffs:
    #         df = df[playoff_index + 1 :]
    #     else:
    #         df = df[:playoff_index]
    #     # df["DATE"] = df["DATE"].apply(lambda x: pd.to_datetime(x))
    #     df["DATE"] = pd.to_datetime(df["DATE"])
    return df


def get_standings(date=None):
    if date is None:
        date = datetime.now()
    else:
        date = pd.to_datetime(date)
    d = {}
    soup = get_wrapper(
        f"https://www.basketball-reference.com/friv/standings.fcgi?month={date.month}&day={date.day}&year={date.year}"
    )
    if soup:
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
            str(team["href"]).replace(".html", "").replace("/teams/", "").split("/")[0]
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


def get_four_factors(url_suffix):

    url = f"https://www.basketball-reference.com{url_suffix}"
    soup = get_wrapper(url)

    div = soup.find("div", {"id": "div_four_factors"})
    if div is None:
        return None
    table = div.find("table", {"id": "four_factors"})
    if table is None:
        return None
    table_body = table.find_all("tbody")
    rows = table_body[0].find_all("tr")

    game_date_str = url_suffix.replace("/boxscores/", "").replace(".html", "")[:-4]
    game_date = datetime.strptime(game_date_str, "%Y%m%d")

    away_ff_row = build_ff_list(rows[0], game_date, False)
    home_row = build_ff_list(rows[1], game_date, True)

    df = pd.DataFrame(
        [away_ff_row, home_row],
        columns=[
            "GAME_DATE",
            "HOME",
            "TEAM",
            "PACE",
            "EFG",
            "TOV",
            "ORB",
            "FT_FGA",
            "OFF_RTG",
        ],
    )
    df["PACE"] = df["PACE"].astype(float)
    df["EFG"] = df["EFG"].astype(float)
    df["TOV"] = df["TOV"].astype(float)
    df["ORB"] = df["ORB"].astype(float)
    df["FT_FGA"] = df["FT_FGA"].astype(float)
    df["OFF_RTG"] = df["OFF_RTG"].astype(float)
    df.reset_index(drop=True, inplace=True)

    return df


def get_four_factors_for_season(schedule, start, end):
    final_df: pd.DataFrame = None
    for index, row in schedule.iterrows():
        if row["HOME_PTS"] == "":
            continue

        if pd.Timestamp(row["DATE"]) >= pd.Timestamp(start) and pd.Timestamp(
            row["DATE"]
        ) <= pd.Timestamp(end):
            print(row["DATE"])
            url_suffix = row["BOX_SCORE_LINK"]
            df: pd.DataFrame = get_four_factors(url_suffix)
            time.sleep(random.randint(5, 10))
            if df is None:
                continue
            if index == 0:
                final_df = df
            else:
                final_df = pd.concat([final_df, df])

    return final_df


def get_four_factors_for_season_full(season_end_year, start, end):
    schedule: pd.DataFrame = get_schedule(season_end_year)

    final_df: pd.DataFrame = None
    for index, row in schedule.iterrows():
        if row["HOME_PTS"] == "":
            continue

        if row["DATE"] >= pd.Timestamp(start) and row["DATE"] <= pd.Timestamp(end):
            print(row["DATE"])
            url_suffix = row["BOX_SCORE_LINK"]
            df: pd.DataFrame = get_four_factors(url_suffix)
            time.sleep(random.randint(5, 10))
            if df is None:
                continue
            if index == 0:
                final_df = df
            else:
                final_df = pd.concat([final_df, df])

    return final_df


def build_ff_list(row, game_date, is_home_team):
    teams = row.find_all("th")
    if teams[0].get("data-stat") == "team_id":
        team = teams[0].next.text

    cols = row.find_all("td")
    for col in cols:
        if col.get("data-stat") == "pace":
            pace = col.text
        if col.get("data-stat") == "efg_pct":
            efg_pct = col.text
        if col.get("data-stat") == "tov_pct":
            tov_pct = col.text
        if col.get("data-stat") == "orb_pct":
            orb_pct = col.text
        if col.get("data-stat") == "ft_rate":
            ft_rate = col.text
        if col.get("data-stat") == "off_rtg":
            off_rtg = col.text
    ff_list = [
        game_date,
        is_home_team,
        team,
        pace,
        efg_pct,
        tov_pct,
        orb_pct,
        ft_rate,
        off_rtg,
    ]
    return ff_list
