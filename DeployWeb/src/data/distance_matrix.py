import googlemaps
import numpy as np
import pandas as pd

from city.load_cities import CITIES
from load_key import api_key


gmaps = googlemaps.Client(key=api_key)

df_coordinates = CITIES[1].df_coordinates
df_coordinates.rename(columns={'Unnamed: 0': 'station_id'}, inplace=True)


# Necessaire pour contourner les limitations de l'API Distance Matrix (10 éléments max)
def divide_elements(elements, max_size):
    """Diviser une liste d'éléments en sous-listes de taille maximale."""
    for i in range(0, len(elements), max_size):
        yield elements[i:i + max_size]


def compute_distances(df):
    """Compute the distance matrix between stations."""
    stations = df[['latitude', 'longitude']].apply(lambda x: f"{x.latitude},{x.longitude}", axis=1).tolist()
    distances = np.zeros((len(stations), len(stations)), dtype=object)

    for lot_origines in divide_elements(stations, 10): 
        for lot_destinations in divide_elements(stations, 10):
            matrix = gmaps.distance_matrix(lot_origines, lot_destinations, mode='bicycling') # API Call
            for i, row in enumerate(matrix['rows']):
                for j, element in enumerate(row['elements']):
                    if element['status'] == 'OK':
                        distances[stations.index(lot_origines[i])][stations.index(lot_destinations[j])] = element['distance']['text']
                    else:
                        distances[stations.index(lot_origines[i])][stations.index(lot_destinations[j])] = None
    return distances


distances = compute_distances(df_coordinates)
df_distances = pd.DataFrame(distances, index=df_coordinates['station_id'], columns=df_coordinates['station_id'])
df_distances.to_csv('distances_entre_stations.csv')
print("Matrice des distances sauvegardée.")