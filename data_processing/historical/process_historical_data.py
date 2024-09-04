import os
import pandas as pd
from typing import Dict

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import optuna

from ..constants import BASE_URL, DATA_DIR
from ..tools.utils import get_actual_season_start_year, get_past_seasons_years
from ..tools.fpl_api import get_base_api_data, load_fixtures
from .hist_team_selection import select_my_team
from ..tools.metrics import get_metrics


class HistoricalDataProcessor:
    def __init__(self):
        self.elements_df = get_base_api_data("elements")  # mostly info about PLAYERS from actual season
        self.element_types_df = get_base_api_data("element_types")
        self.teams_df = get_base_api_data("teams")
        self.selected_team = None
        self.model = xgb.XGBRegressor()
        self.launch_pipeline()

    def launch_pipeline(self):
        past_seasons = HistoricalDataProcessor.get_past_season_dates()
        prev_season_df = self.prepare_dataset(os.path.join(DATA_DIR, "historical", past_seasons['prev']))
        last_season_df = self.prepare_dataset(os.path.join(DATA_DIR, "historical", past_seasons['last']))
        # Train and fine-tune the model on data from last 2 seasons
        self.train_model(prev_season_df, last_season_df, predict_attr="points_per_game")

        actual_set = self.prepare_dataset_from_api()
        X_actual = actual_set.drop('points_per_game', axis=1)
        y_actual_preds = self.model.predict(X_actual).round(1)

        candidates_df = actual_set.drop('points_per_game', axis=1)
        candidates_df["predicted_ppg"] = y_actual_preds.round(2)
        candidates_df["predicted_value"] = candidates_df["predicted_ppg"] / candidates_df["now_cost"] * 10
        candidates_df_filtered = self.clean_candidates_dataset(candidates_df)
        # Finally select the team based on AI predictions
        self.selected_team = select_my_team(candidates_df_filtered)

    @staticmethod
    def get_past_season_dates() -> Dict[str, str]:
        fixtures_df = load_fixtures()
        act_start_year = get_actual_season_start_year(fixtures_df)
        past_seasons_dates = get_past_seasons_years(act_start_year)
        return past_seasons_dates

    def clean_candidates_dataset(self, candidates_df: pd.DataFrame):
        candidates_df.team = candidates_df.team.astype(int)
        candidates_df.id = candidates_df.id.astype(int)
        candidates_df.element_type = candidates_df.element_type.astype(int)

        candidates_df['team_name'] = self.elements_df.team.map(self.teams_df.set_index('id').name)
        candidates_df['position'] = self.elements_df.element_type.map(self.element_types_df.set_index('id').singular_name)
        candidates_df['first_name'] = self.elements_df.id.map(self.elements_df.set_index('id').first_name)
        candidates_df['second_name'] = self.elements_df.id.map(self.elements_df.set_index('id').second_name)

        # Cut off players not expected to be playing
        threshold = 0.6 * candidates_df['starts'].max()
        candidates_df_filtered = candidates_df[candidates_df['starts'] >= threshold]

        return candidates_df_filtered

    def train_model(self, prev_season_data: pd.DataFrame, last_season_data: pd.DataFrame, predict_attr: str):
        X_train = prev_season_data.drop(predict_attr, axis=1)
        y_train = prev_season_data[predict_attr]

        val_set, test_set = train, test = train_test_split(last_season_data, test_size=0.4)
        X_val = val_set.drop(predict_attr, axis=1)
        y_val = val_set[predict_attr]

        X_test = test_set.drop(predict_attr, axis=1)
        y_test = test_set[predict_attr]

        self.model.fit(X_train, y_train)
        # Optionally log the metrics
        y_preds = self.model.predict(X_test).round(1)
        get_metrics(y_test, y_preds)

        # for Optuna optimization
        def objective(trial):
            params = {
                "objective": "reg:squarederror",
                "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
                "max_depth": trial.suggest_int("max_depth", 1, 10),
            }
            model = xgb.XGBRegressor(**params)
            model.fit(X_train, y_train, verbose=False)
            predictions = model.predict(X_val)
            rmse = mean_squared_error(y_val, predictions, squared=False)
            return rmse

        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=100)
        print('Best hyperparameters:', study.best_params)
        print('Best RMSE:', study.best_value)

        self.model = xgb.XGBRegressor(**study.best_params)
        self.model.fit(X_train, y_train, verbose=False)

        # Optionally log the metrics
        y_preds = self.model.predict(X_test).round(1)
        get_metrics(y_test, y_preds)

    def prepare_dataset(self, dir_path: str):
        # Relevant
        teams_map_df = pd.read_csv(os.path.join(dir_path, "teams.csv"), index_col=False)
        players_df = pd.read_csv(os.path.join(dir_path, "players_raw.csv"))
        players_df['team_name'] = players_df.team.map(teams_map_df.set_index('id').name)
        players_df['position'] = players_df.element_type.map(self.element_types_df.set_index('id').singular_name)
        players_df['team_strength'] = players_df.team.map(teams_map_df.set_index('id').strength)

        player_filtered = [
            'id', 'team', 'now_cost', 'expected_goal_involvements', 'expected_goals_conceded', 'ict_index',
            'element_type', 'team_strength', 'points_per_game', 'starts', 'minutes']  # 'transfers_in', 'transfers_out'

        players_df_filtered = players_df[player_filtered]
        players_df_filtered.dropna()

        print(f"\nDataset created! Source: {dir_path}\n")

        return players_df_filtered

    def prepare_dataset_from_api(self):
        # supplement actual data
        self.elements_df['team_name'] = self.elements_df.team.map(self.teams_df.set_index('id').name)
        self.elements_df['position'] = self.elements_df.element_type.map(self.element_types_df.set_index('id').singular_name)
        self.elements_df['team_strength'] = self.elements_df.team.map(self.teams_df.set_index('id').strength)

        # Move to constants?
        player_filtered = ['id', 'team', 'now_cost', 'expected_goal_involvements', 'expected_goals_conceded',
                           'ict_index', 'element_type', 'team_strength', 'points_per_game', 'starts', 'minutes']

        players_df_filtered = self.elements_df[player_filtered]
        players_df_filtered.dropna()

        # convert all values to numerical ones
        for col_name in players_df_filtered.columns:
            players_df_filtered[col_name] = players_df_filtered[col_name].astype(float)

        print(f"\nDataset created! Source: {BASE_URL}\n")
        return players_df_filtered
