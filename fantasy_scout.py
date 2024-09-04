import os
import pandas as pd

from datetime import datetime
from typing import Optional
from pathlib import Path

from data_processing.constants import PLAYER_PROFILE
from data_processing.tools.fpl_api import how_many_gws_passed, load_fixtures
from data_processing.actual.process_actual_data import ActualDataProcessor
from data_processing.historical.process_historical_data import HistoricalDataProcessor
from tools import find_matchups

# How many GWs should pass to consider data from ongoing season relatable
MIN_RELATABLE_GWS = 5


class FantasyScout:
    def __init__(self):
        self.my_team: Optional[pd.DataFrame] = None
        self.save_dir = os.path.join(os.getcwd(), "results")

    @staticmethod
    def select_team():
        if FantasyScout.check_if_in_season():
            return FantasyScout.run_in_season_pipeline()
        else:
            return FantasyScout.run_preseason_pipeline()

    @staticmethod
    def check_if_in_season():
        """
        If the 5th GW has passed, it is relatable to analyze data from the current season.
        If not, predict points with AI models trained on historical data

        :return: boolean, True if at least [MIN_RELATABLE_GWS] GWs passed, otherwise False
        """
        fixtures_df = load_fixtures()
        past_gws_count = how_many_gws_passed(fixtures_df)
        return past_gws_count >= MIN_RELATABLE_GWS

    @staticmethod
    def run_preseason_pipeline():
        preseason_engine = HistoricalDataProcessor()
        preseason_engine.launch_pipeline()
        return preseason_engine.selected_team

    @staticmethod
    def run_in_season_pipeline():
        in_season_engine = ActualDataProcessor()
        in_season_engine.launch_pipeline()
        print(f"Collected {len(in_season_engine.selected_team)} players")
        return in_season_engine.selected_team

    def save_to_excel(self, team_df: pd.DataFrame):
        Path(self.save_dir).mkdir(parents=True, exist_ok=True)
        ds = datetime.today().strftime('%Y-%m-%d')
        file_name = f"{ds}-FPL-MyTeam.xlsx"
        team_df.to_excel(os.path.join(self.save_dir, file_name))

    @staticmethod
    def calc_fixtures(my_team: pd.DataFrame):
        fixtures_df = load_fixtures()
        future_fixtures_df = fixtures_df[fixtures_df["finished"] == False]
        my_team['fixtures_difficulty'] = my_team.apply(lambda row: find_matchups(future_fixtures_df, row), axis=1)
        return my_team

    @staticmethod
    def add_comments(my_team: pd.DataFrame):
        my_team["comments"] = None

        for position in PLAYER_PROFILE.keys():
            tmp = my_team[my_team['position'] == position]
            max_index = tmp['fixtures_difficulty'].idxmax()
            my_team.at[max_index, 'comments'] = "Consider benching (hard matchups)"

        worst_performer_idx = my_team.index[-1]
        my_team.at[worst_performer_idx, 'comments'] = "Consider benching/selling (worst performing)"

        min_index = my_team['fixtures_difficulty'].idxmin()
        my_team.at[min_index, 'comments'] = "Consider captaining (easiest matchups)"

        max_index = my_team['now_cost'].idxmax()
        my_team.at[max_index, 'comments'] = "Consider captaining (biggest star)"

        return my_team


def main():
    scout = FantasyScout()
    scout.my_team = FantasyScout.select_team()
    scout.my_team = FantasyScout.calc_fixtures(scout.my_team)
    scout.my_team = FantasyScout.add_comments(scout.my_team)
    scout.save_to_excel(scout.my_team)
    print(f"ALL DONE! Please check your results here: {scout.save_dir}")


if __name__ == "__main__":
    main()
