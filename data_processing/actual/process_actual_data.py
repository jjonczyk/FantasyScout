from typing import Dict, Any, List

import pandas as pd
import numpy as np

from .act_team_selection import select_my_team
from ..constants import DEF, OFF
from ..tools.fpl_api import get_base_api_data, load_fixtures

# How many next/future GameWeeks should be considered in selecting teams
FUTURE_GW_LIMIT = 5
# How many if the best defensive/offensive teams should be considered
TEAMS_LIMIT = 7


class ActualDataProcessor:
    def __init__(self):
        self.elements_df = get_base_api_data("elements")
        self.element_types_df = get_base_api_data("element_types")
        self.teams_df = get_base_api_data("teams")
        self.events_df = get_base_api_data("events")
        self.fixtures_df = load_fixtures()
        self.selected_team = None
        self.matchups_df = None
        self.launch_pipeline()

    def launch_pipeline(self):
        # Add human-readable info and augment the data
        self.augment_elements_df()

        # Collect fixtures for next GWs
        fixtures_future_df = self.fixtures_df[self.fixtures_df["finished"] == False]
        fixtures_future_df = fixtures_future_df[~np.isnan(fixtures_future_df['event'])]  # Filter out some garbage
        # Add info about home/away performance for next GWs
        self.collect_matchups(fixtures_future_df)
        self.augment_matchups()
        self.calc_relative_strength()

        teams_idx = self.get_team_off_def_idx()
        def_teams = self.get_best_teams(teams_idx, profile=DEF)
        off_teams = self.get_best_teams(teams_idx, profile=OFF)

        self.selected_team = select_my_team(self.elements_df, def_teams, off_teams)
        print(f"Collected {len(self.selected_team)}")


    def augment_elements_df(self) -> None:
        # elements_df - mostly players' data
        self.elements_df['position'] = self.elements_df.element_type.map(
        self.element_types_df.set_index('id').singular_name)
        self.elements_df['team_name'] = self.elements_df.team.map(self.teams_df.set_index('id').name)
        self.elements_df["form"] = pd.to_numeric(self.elements_df['form'])
        self.elements_df["points_per_game"] = pd.to_numeric(self.elements_df['points_per_game'])
        self.elements_df["form_ppg"] = (self.elements_df["form"] + self.elements_df["points_per_game"]) / 2
        self.elements_df["value_season"] = pd.to_numeric(self.elements_df['value_season'])


    def collect_matchups(self, fixtures_future_df: pd.DataFrame) -> None:
        matchup_info = ['event', 'team_a', 'team_h']
        self.matchups_df = fixtures_future_df[matchup_info]

    def augment_matchups(self) -> None:
        self.matchups_df.loc[:, 'team_a_name'] = self.matchups_df.team_a.map(self.teams_df.set_index('id').name)
        self.matchups_df.loc[:, 'team_h_name'] = self.matchups_df.team_h.map(self.teams_df.set_index('id').name)
        self.matchups_df.loc[:, 'team_a_strength'] = self.matchups_df.team_a.map(self.teams_df.set_index('id').strength)
        self.matchups_df.loc[:, 'team_h_strength'] = self.matchups_df.team_h.map(self.teams_df.set_index('id').strength)
        self.matchups_df.loc[:, 'team_a_strength_away'] = self.matchups_df.team_a.map(
            self.teams_df.set_index('id').strength_overall_away)
        self.matchups_df.loc[:, 'team_h_strength_home'] = self.matchups_df.team_h.map(
            self.teams_df.set_index('id').strength_overall_home)
        self.matchups_df.loc[:, 'team_a_strength_att_away'] = self.matchups_df.team_a.map(
            self.teams_df.set_index('id').strength_attack_away)
        self.matchups_df.loc[:, 'team_h_strength_def_home'] = self.matchups_df.team_h.map(
            self.teams_df.set_index('id').strength_defence_home)
        self.matchups_df.loc[:, 'team_a_strength_def_away'] = self.matchups_df.team_a.map(
            self.teams_df.set_index('id').strength_defence_away)
        self.matchups_df.loc[:, 'team_h_strength_att_home'] = self.matchups_df.team_h.map(
            self.teams_df.set_index('id').strength_attack_home)

    def calc_relative_strength(self) -> None:
        # score showing teams strength diff
        self.matchups_df.loc[:, "team_h_strength_diff"] = (
                self.matchups_df["team_h_strength"] - self.matchups_df["team_a_strength"]
        )
        # as above, but take into account home/away performance
        self.matchups_df.loc[:, "team_h_str_ovr_diff"] = (
                self.matchups_df["team_h_strength_home"] - self.matchups_df["team_a_strength_away"]
        )
        # score for forwards/midfielders
        self.matchups_df.loc[:, "team_h_str_att_diff"] = (
                self.matchups_df["team_h_strength_att_home"] - self.matchups_df["team_a_strength_def_away"]
        )
        # score for defenders/goalkeepers
        self.matchups_df.loc[:, "team_h_str_def_diff"] = (
                self.matchups_df["team_h_strength_def_home"] - self.matchups_df["team_a_strength_att_away"]
        )

    def get_team_off_def_idx(self) -> Dict[Any, Dict[str, Any]]:
        teams_idx = dict()  # "id": {"name": str, "DEF_IDX": (int), "OFF_IDX": (int)}

        for i in range(len(self.teams_df)):
            team_id = self.teams_df.iloc[i, self.teams_df.columns.get_loc("id")]
            teams_idx[team_id] = dict()

            team_name = self.teams_df.iloc[i, self.teams_df.columns.get_loc("name")]
            teams_idx[team_id]["name"] = team_name
            # print(f"{team_code}: {team}")

            team_matchups_df = self.matchups_df[(self.matchups_df['team_a'] == team_id) | (self.matchups_df['team_h'] == team_id)]
            teams_idx[team_id]["DEF_IDX"] = 0
            teams_idx[team_id]["OFF_IDX"] = 0

            for _, row in team_matchups_df.head(FUTURE_GW_LIMIT).iterrows():
                if team_id == row["team_h"]:
                    # DEFENSIVE += team_h_str_def_diff
                    # OFFENSIVE += team_h_str_att_diff
                    teams_idx[team_id]["DEF_IDX"] += row['team_h_str_def_diff']
                    teams_idx[team_id]["OFF_IDX"] += row['team_h_str_att_diff']
                else:  # team_a
                    # DEFENSIVE -= team_h_str_att_diff (att_h = -def_a)
                    # OFFENSIVE -= team_h_str_def_diff (def_h = -att_a)
                    teams_idx[team_id]["DEF_IDX"] -= row['team_h_str_att_diff']
                    teams_idx[team_id]["OFF_IDX"] -= row['team_h_str_def_diff']
        return teams_idx

    @staticmethod
    def get_best_teams(teams_idx, profile: str, teams_limit: int = TEAMS_LIMIT) -> List[str]:
        if profile == DEF:
            # The best matchups for defence
            def_teams = sorted(teams_idx.keys(), key=lambda x: (teams_idx[x]['DEF_IDX']), reverse=True)[:teams_limit]
            teams = [teams_idx[x]['name'] for x in def_teams]
        elif profile == OFF:
            # The best matchups for offence
            off_teams = sorted(teams_idx.keys(), key=lambda x: (teams_idx[x]['OFF_IDX']), reverse=True)[:teams_limit]
            teams = [teams_idx[x]['name'] for x in off_teams]
        else:
            raise ValueError(f"Invalid team profile, choose one from [{DEF}, {OFF}]")
        return teams
