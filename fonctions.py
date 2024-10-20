import pandas as pd

def calculate_active_time(df):
    df.loc[:, 'time_diff'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
    df.loc[:, 'time_diff'] = df['time_diff'].apply(lambda x: x if x <= 300 else 0)
    total_active_time = df['time_diff'].sum()
    return total_active_time / 60  # Retourner en minutes

def calculate_total_distance(df):
    return df['distance'].iloc[-1] / 1000  # Conversion en km

def filter_by_date(df, start_date, end_date):
    # Convertir start_date et end_date en datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
    return df[mask].copy()  # Créer une copie explicite

# Fonction pour convertir un temps en minutes décimales au format min:sec
def format_duration(minutes):
    mins = int(minutes)
    secs = int((minutes - mins) * 60)
    return f"{mins}:{secs:02d}"  # Affichage au format min:sec

def calculate_heart_rate_zones(df, determine_zone):
    if 'heart_rate' not in df or 'timestamp' not in df:
        return {}  # Retourne un dictionnaire vide si les colonnes sont manquantes

    # Ajouter une colonne 'zone' pour chaque enregistrement de fréquence cardiaque
    df['zone'] = df['heart_rate'].apply(determine_zone)

    # Calculer la durée de chaque enregistrement en secondes
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds().fillna(0)

    # Calculer le temps dans chaque zone
    time_in_zones = df.groupby('zone')['time_diff'].sum() / 60  # Conversion en minutes

    return time_in_zones.to_dict()  # Retourner sous forme de dictionnaire

def calculate_weekly_distance(activities):
    activities_df = pd.DataFrame(activities)
    activities_df['date'] = pd.to_datetime(activities_df['date'])
    
    # Extraire la semaine et l'année
    activities_df['week'] = activities_df['date'].dt.isocalendar().week
    activities_df['year'] = activities_df['date'].dt.year
    
    # Calculer la distance totale par semaine
    weekly_distance = activities_df.groupby(['year', 'week'])['distance (km)'].sum().reset_index()
    return weekly_distance

def calculate_time_above_90_percent_vma(df, vma=14):
    # Assurer que la colonne 'timestamp' est au format datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Vitesse correspondant à 90% de la VMA
    threshold_speed = (0.90 * vma) / 3.6  # Conversion de km/h en m/s

    # Identifier les moments où la vitesse est supérieure à 90% de la VMA
    df['moving'] = df['speed'] > threshold_speed

    # Calculer le temps en mouvement
    df['moving_time'] = df['timestamp'].diff().dt.total_seconds().where(df['moving']).fillna(0) / 60  # Temps en minutes

    # Retourner le temps total au-dessus de 90% de la VMA
    return df['moving_time'].sum()
