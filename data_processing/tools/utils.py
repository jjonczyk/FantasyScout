import pandas as pd
from typing import Dict, List, Any

from data_processing.constants import LIMITS


def check_total_limit_reached(my_team: List[Any]) -> bool:
    """Check if the total limit of players per team has been reached"""
    if len(my_team) < LIMITS['all']:
        return False
    else:
        print(f"Total limit reached")
        print(f"Team collected! :)")
        print("\n\n")
        return True


def get_actual_season_start_year(fixtures_df: pd.DataFrame) -> str:
    """Return the year in which the current season started or will start (if not yet - preseason)"""
    if fixtures_df.iloc[0]['finished']:
        # analyzed season's first event is over - we are during or past this one
        if fixtures_df.iloc[-1]['finished']:
            # It was a previous season so the new one starts the same year
            start_new = fixtures_df.iloc[-1]['kickoff_time'][:4]
        else:
            # We are in-season
            start_new = fixtures_df.iloc[0]['kickoff_time'][:4]
    else:
        # it's a pre-season
        start_new = fixtures_df.iloc[0]['kickoff_time'][:4]
    return start_new


def get_past_seasons_years(new_season_start: str) -> Dict[str, str]:
    """Return a dictionary containing the names (years) of the last two seasons"""
    result = {
        "prev": f"{str(int(new_season_start)-2)}-{str(int(new_season_start)-1)[2:4]}",
        "last": f"{str(int(new_season_start)-1)}-{new_season_start[2:4]}"
    }
    return result