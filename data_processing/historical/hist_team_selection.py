from typing import Dict

import pandas as pd

from ..constants import LIMITS
from ..tools.utils import check_total_limit_reached

# Check team limits
def check_one_team_limit_reached(clubs_usage: Dict[str, int], team: str, player_data: pd.Series):
    check = False
    if clubs_usage.get(team):
        if clubs_usage[team] >= LIMITS['one_team']:
            print(
                f"Rejected: {player_data['first_name']} {player_data['second_name']} from {team} exceeded the limit for same team players")
            check = True
    else:
        clubs_usage[team] = 0
    return check, clubs_usage


# Check position limits
def check_position_limit_reached(position_usage: Dict[str, int], position: str, player_data: pd.Series):
    check = False
    if position_usage.get(position):
        if position_usage[position] >= LIMITS['position'][position]:
            print(f"Rejected: {player_data['first_name']} {player_data['second_name']}'s position: {position} "
                  f"exceeded the limit: {LIMITS['position'][position]}")
            check = True
    else:
        position_usage[position] = 0
    return check, position_usage


def get_best_players(players_df: pd.DataFrame, condition: str, position=None, n=1) -> pd.DataFrame:
    if condition == "value":
        target = 'predicted_value'
        threshold = 0.75 * players_df['now_cost'].max()
        players_df = players_df[players_df['now_cost'] < threshold]
    elif condition == "performance":
        target = 'predicted_ppg'
    else:
        raise ValueError("Invalid condition, please choose from: ['value'/'performance']")

    players_df = players_df.sort_values(by=target, ascending=False)
    if position:
        players_df = players_df[players_df['position'] == position]

    print(f"Found best {condition} player(s) | Target position? {position}")
    best_player = players_df.head(n)
    return best_player


def select_my_team(candidates_df: pd.DataFrame) -> pd.DataFrame:
    my_team = list()
    for bp_limit in range(LIMITS['all'] + 1):
        wallet = 1000

        selected_ids = set()
        prev_team = my_team
        clubs_usage = dict()
        position_usage = dict()
        my_team = list()
        bp_counter = 0

        PERF_IDX = 0
        VALUE_IDX = 1
        suggested_candidates = {
            PERF_IDX: get_best_players(candidates_df, condition='performance', n=10 * bp_limit),
            VALUE_IDX: get_best_players(candidates_df, condition='value', n=20 * LIMITS['all']),
        }

        for condition, found_players in (suggested_candidates.items()):
            for i, player_data in found_players.iterrows():

                if player_data['id'] in selected_ids:
                    continue
                if check_total_limit_reached(my_team):
                    break

                position = player_data["position"]
                team = player_data["team_name"]

                # Check other limits
                team_limit, clubs_usage = check_one_team_limit_reached(clubs_usage, team, player_data)
                if team_limit:
                    continue
                position_limit, position_usage = check_position_limit_reached(position_usage, position, player_data)
                if position_limit:
                    continue

                # Best performing players - check limit, update counter
                if condition == PERF_IDX:
                    if bp_counter >= bp_limit:
                        print("The best performing players limit reached")
                        break
                    bp_counter += 1

                # Update wallet
                print(
                    f"Approved: {player_data['first_name']} {player_data['second_name']} ({position}@{team}) added to team")
                my_team.append(player_data)
                selected_ids.add(player_data['id'])
                print(f"Collected players: {len(my_team)}")
                clubs_usage[team] += 1
                position_usage[position] += 1
                wallet -= player_data['now_cost']
                print(f"Budget remained: {wallet}")

                if wallet < 0:
                    my_team = prev_team
                    return pd.DataFrame(my_team)
