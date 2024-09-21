import unittest
from typing import List

from basketball_reference_scraper.seasons import get_schedule, get_standings


class TestSeason(unittest.TestCase):

    _expected_schedule_columns: List[str] = [
        "DATE",
        "VISITOR",
        "VISITOR_PTS",
        "HOME",
        "HOME_PTS",
        "OT?",
        "LOG",
    ]

    _expected_standings_columns: List[str] = [
        "TEAM",
        "W",
        "L",
        "W/L%",
        "GB",
        "PW",
        "PL",
        "PS/G",
        "PA/G",
    ]

    _conferences: List[str] = ["EASTERN_CONF", "WESTERN_CONF"]

    def test_get_schedule(self):
        df = get_schedule(1999)

        self.assertListEqual(list(df.columns), self._expected_schedule_columns)

    def test_get_schedule_weird_season(self):
        for season in (1971, 1953):
            for use_playoffs in (True, False):
                cur_season = get_schedule(season, playoffs=use_playoffs)
                self.assertListEqual(
                    list(cur_season.columns), self._expected_schedule_columns
                )

    def test_get_standings(self):
        d = get_standings()
        self.assertListEqual(list(d.keys()), self._conferences)

        df = d["WESTERN_CONF"]

        self.assertListEqual(list(df.columns), self._expected_standings_columns)

    def test_get_standings_weird_season(self):
        for season in (1971, 1953):
            d = get_standings(season)
            self.assertListEqual(list(d.keys()), self._conferences)

            df = d["WESTERN_CONF"]
            self.assertListEqual(list(df.columns), self._expected_standings_columns)


if __name__ == "__main__":
    unittest.main()
