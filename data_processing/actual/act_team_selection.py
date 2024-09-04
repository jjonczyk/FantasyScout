from typing import Optional, List
import pandas as pd

from data_processing.constants import LIMITS, DEF, PLAYER_PROFILE
from ..tools.utils import check_total_limit_reached

# Mostly for human-readable purposes
PLAYER_DETAIL_COLS = [
    'id','first_name','second_name', 'element_type', 'position', 'team', 'team_name', 'ict_index', 'ict_index_rank', 'total_points', 'now_cost', 'value_season',
    'chance_of_playing_next_round', 'chance_of_playing_this_round', 'points_per_game', 'selected_by_percent',
    'expected_goal_involvements', 'value_form', 'expected_goals_conceded', 'penalties_order', 'starts',
    'form', 'bps', 'minutes', 'clean_sheets', "form_ppg"
]

# Under what aspect should players be selected
AVAILABLE_TARGETS = ["budget", "performance"]

def get_players_by_target(players_df: pd.DataFrame, criterium: str, limit: int = 100) -> pd.DataFrame:
    found_players = players_df.sort_values(criterium, ascending=False)[PLAYER_DETAIL_COLS]
    return found_players[:limit]


def find_best_players(
        players_df: pd.DataFrame, target: str, position: Optional[str] = None, limit: int = 100
) -> pd.DataFrame:
    if position and position not in PLAYER_PROFILE:
        raise ValueError(f"Invalid position: '{position}'. Allowed values are: {PLAYER_PROFILE.keys()}")
    if target not in AVAILABLE_TARGETS:
        raise ValueError(f"Invalid position: '{target}'. Allowed values are: {AVAILABLE_TARGETS}")

    if position:
        players_df = players_df[players_df['element_type'] == position]

    # Filter out players who may not play this round
    # NaN doesn't mean not playing - often the opposite (injuries are immediately provided as numerical values)
    players_df['chance_of_playing_this_round'] = players_df['chance_of_playing_this_round'].fillna(75)
    players_df = players_df[players_df['chance_of_playing_this_round'] >= 75]

    if target == "performance":
        players_df["form"] = pd.to_numeric(players_df['form'])
        players_df["points_per_game"] = pd.to_numeric(players_df['points_per_game'])
        players_df["form_ppg"] = (players_df["form"] + players_df["points_per_game"]) / 2
        found_players = get_players_by_target(players_df, criterium="form_ppg", limit=limit)

    else:  # target ==  "budget"
        found_players = get_players_by_target(players_df, criterium="value_season", limit=limit)
        threshold = 0.75 * found_players['now_cost'].max()
        found_players = found_players[found_players['now_cost'] < threshold]

    return found_players


def select_my_team(elements_df: pd.DataFrame, def_teams: List[str], off_teams: List[str]) -> pd.DataFrame:
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
            PERF_IDX: find_best_players(elements_df, target="performance"),
            VALUE_IDX: find_best_players(elements_df, target="budget"),
        }
        for condition, found_players in (suggested_candidates.items()):
            for i, player_data in found_players.iterrows():

                if player_data['id'] in selected_ids:
                    continue
                if check_total_limit_reached(my_team):
                    break

                position = player_data["position"]
                team = player_data["team_name"]

                # Check if profile in preferred team - optionally!
                profile = PLAYER_PROFILE[position]
                if profile == DEF:
                    if team not in def_teams:
                        print(
                            f"Rejected: {player_data['first_name']} {player_data['second_name']} | {position}@{team} is not {profile} enough")
                        continue
                else:  # profile == OFF
                    if team not in off_teams:
                        print(
                            f"Rejected: {player_data['first_name']} {player_data['second_name']} | {position}@{team} is not {profile} enough")
                        continue

                # Check team limits
                if clubs_usage.get(team):
                    if clubs_usage[team] >= LIMITS['one_team']:
                        print(
                            f"Rejected: {player_data['first_name']} {player_data['second_name']} | {position}@{team} exceeded the limit for same team players: {LIMITS['one_team']}")
                        continue
                else:
                    clubs_usage[team] = 0

                # Check position limits
                if position_usage.get(position):
                    if position_usage[position] >= LIMITS['position'][position]:
                        print(
                            f"Rejected: {player_data['first_name']} {player_data['second_name']}'s position: {position} "
                            f"exceeded the limit: {LIMITS['position'][position]}"
                        )
                        continue
                else:
                    position_usage[position] = 0

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
