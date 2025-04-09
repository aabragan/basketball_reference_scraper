from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup
from requests import get

from basketball_reference_scraper.teams import get_team_games

try:
    from request_utils import get_wrapper
    from utils import format_html
except:
    from basketball_reference_scraper.request_utils import get_wrapper
    from basketball_reference_scraper.utils import format_html


def get_pbp_helper(suffix):
    selector = f"#pbp"
    soup = get_wrapper(f"https://www.basketball-reference.com/boxscores/pbp{suffix}")
    if soup:
        table = soup.find("table", attrs={"id": "pbp"})
        return pd.read_html(format_html(table))[0]
    else:
        raise ConnectionError("Request to basketball reference failed")


def format_df(df1):
    df1.columns = list(map(lambda x: x[1], list(df1.columns)))
    t1 = list(df1.columns)[1].upper()
    t2 = list(df1.columns)[5].upper()
    q = 0
    df = None
    for index, row in df1.iterrows():
        d = {
            "QUARTER": float("nan"),
            "TIME_REMAINING": float("nan"),
            f"{t1}_ACTION": float("nan"),
            f"{t2}_ACTION": float("nan"),
            f"{t1}_SCORE": float("nan"),
            f"{t2}_SCORE": float("nan"),
        }
        # if row["Time"] == "2nd Q":
        #     q = 2
        # elif row["Time"] == "3rd Q":
        #     q = 3
        # elif row["Time"] == "4th Q":
        #     q = 4
        # elif "OT" in row["Time"]:
        #     q = row["Time"][0] + "OT"
        if row.iloc[0] == "12:00.0":
            q += 1
        try:
            d["QUARTER"] = q
            d["TIME_REMAINING"] = row.iloc[0]
            scores = row["Score"].split("-")
            d[f"{t1}_SCORE"] = int(scores[0])
            d[f"{t2}_SCORE"] = int(scores[1])
            d[f"{t1}_ACTION"] = row[list(df1.columns)[1]]
            d[f"{t2}_ACTION"] = row[list(df1.columns)[5]]
            if df is None:
                df = pd.DataFrame(columns=list(d.keys()))
            df = df.append(d, ignore_index=True)
        except:
            continue
    return df


def get_pbp(date, team1, team2):
    date = pd.to_datetime(date)
    end_year = date.year + 1 if date.month > 9 else date.year
    team_games = get_team_games(team1, end_year, False)
    suffix = team_games[team_games["DATE"] == date.strftime("%Y-%m-%d")][
        "BOX_SCORE_LINK"
    ].iloc[0]
    suffix = suffix.replace("/boxscores", "")
    df = get_pbp_helper(suffix)
    df = format_df(df)
    return df
