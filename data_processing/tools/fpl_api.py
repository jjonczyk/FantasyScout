from typing import Optional

import requests
import pandas as pd

from ..constants import BASE_URL, FIXTURES_ENDPOINT


def get_base_api_data(data_type: str) -> Optional[pd.DataFrame]:
    base_response = requests.get(BASE_URL)
    base_json = base_response.json()
    if not base_json:
        raise ConnectionError(f"Cannot collect data from: {BASE_URL}.\n"
                              f"Please check your connection or the url provided.")
    try:
        data_type_df = pd.DataFrame(base_json[data_type])
        return data_type_df
    except KeyError as err:
        raise KeyError(f"Cannot access {data_type} in the data from: {BASE_URL}. \n{err}")


def load_fixtures() -> pd.DataFrame:
    fixtures_response = requests.get(FIXTURES_ENDPOINT)
    fixtures_json = fixtures_response.json()
    fixtures_df = pd.DataFrame(fixtures_json)
    return fixtures_df


def how_many_gws_passed(fixtures_df: pd.DataFrame) -> int:
        fixtures_past_df = fixtures_df[fixtures_df["finished"] == True]
        # last finished event's ID == how many GWs passed
        return fixtures_past_df['event'].iloc[-1]
