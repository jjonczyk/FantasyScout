import pandas as pd

from typing import Union


def get_difficulty(row: pd.DataFrame, team_id: int) -> Union[int, None]:
    if row['team_a'] == team_id:
        return row['team_a_difficulty']
    elif row['team_h'] == team_id:
        return row['team_h_difficulty']
    else:
        return None


def find_matchups(future_fixtures: pd.DataFrame, player_data: pd.DataFrame, num_of_gws: int = 3) -> int:
    team_id = player_data["team"]
    next_matchups_df = future_fixtures[
        (future_fixtures['team_a'] == team_id) | (future_fixtures['team_h'] == team_id)].head(num_of_gws)

    difficulties = next_matchups_df.apply(get_difficulty, axis=1, team_id=team_id)
    # print(f"Team ID: {team_id}, fixture difficulties: {difficulties.tolist()}")

    return sum(difficulties)
