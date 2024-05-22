import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from data.city.load_cities import City
from data.prediction.forecast_model import ForecastModel
from data.data import get_acp_predictor

class PredictByPCA(ForecastModel):
    name = 'PCA_Reconstruction'

    def __init__(self, city: City, train_size: float=0.7, num_components: int=4) -> None:
        super().__init__(city, train_size)
        self.num_components = num_components 

    def train(self) -> None:
        df = self.train_dataset.copy()
        df['hours'] = df.index.hour
        df['days'] = pd.Categorical(
            values=df.index.day_name(),
            categories=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            ordered=True
        )
        df_mean = df.groupby(['days', 'hours'], observed=True).mean()
        
        acp_results = get_acp_predictor(df_mean, use_transposed=True)
        components = acp_results.pca.components_[:self.num_components]  

        self.model = pd.DataFrame(
            acp_results.pca.transform(df_mean.T)[:,:self.num_components] @ components,  # Reconstruction
            index=df_mean.columns,
            columns=df_mean.index
        ).T  # Transpose so columns are stations

    def predict(self, selected_station: str, data: pd.Series, forecast_length: int) -> pd.Series:
        serie = self.model[selected_station]
        serie.name = PredictByPCA.name

        data_index = ForecastModel.get_DatetimeIndex_forecasting(data, forecast_length)
        tmp_data_index = data_index.to_series().copy().to_frame()
        tmp_data_index['days'] = tmp_data_index.index.day_name()
        tmp_data_index['hours'] = tmp_data_index.index.hour

        predicted_data = serie.reindex_like(tmp_data_index.set_index(['days', 'hours'])).set_axis(data_index)
        clipped_data = predicted_data.clip(lower=0, upper=1)

        return clipped_data
