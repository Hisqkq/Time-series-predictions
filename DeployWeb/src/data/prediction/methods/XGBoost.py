import pandas as pd
from xgboost import XGBRegressor
from os import makedirs
from typing import Self

from data.city.load_cities import City
from data.data import get_interpolated_indices
from data.prediction.forecast_model import ForecastModel, PATH_MODEL

class XGBoost(ForecastModel):
    name = 'XGBoost'

    def __init__(self: Self, city: City, train_size: float = 0.7) -> None:
        super().__init__(city, train_size)
        makedirs(f'{PATH_MODEL}{self.name}', exist_ok=True)
        self.models = {}

    def train(self: Self) -> None:
        df = self.train_dataset.copy()

        for station in df.columns:
            try:
                current_model = self.load_model(station)
            except FileNotFoundError:
                # Exclure les indices interpolés pour la station
                interpolated_indices = get_interpolated_indices(df[station], output_type='mask')
                df_filtered = df.drop(index=interpolated_indices)

                df_X = ForecastModel.create_features_from_date(df_filtered.index.to_series())
                df_y = df_filtered[station]

                current_model = XGBRegressor(n_estimators=70, max_depth=9, learning_rate=0.08)
                current_model.fit(df_X, df_y)

                self.save_model(current_model, station)
            
            self.models[station] = current_model

    def predict(self: Self, selected_station: str, data: pd.Series, forecast_length: int) -> pd.Series:
        if selected_station not in self.models:
            raise ValueError(f'Model for station {selected_station} not found.')

        data_index = ForecastModel.get_DatetimeIndex_forecasting(data, forecast_length)
        df_X_future = ForecastModel.create_features_from_date(data_index.to_series())

        model = self.models[selected_station]
        predictions = model.predict(df_X_future)
        predictions = predictions.clip(0, 1)
        
        return pd.Series(predictions, index=data_index, name=self.name)
