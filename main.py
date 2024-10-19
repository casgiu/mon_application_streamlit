import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os
from config import folder_path, extracted_folder, cleanup_folder
from heart_rate_zones import determine_zone
from data_extraction import process_fit_files  # Importation de la fonction d'extraction

# Fonction pour calculer le temps actif
def calculate_active_time(df):
    df.loc[:, 'time_diff'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
    df.loc[:, 'time_diff'] = df['time_diff'].apply(lambda x: x if x <= 300 else 0)
    total_active_time = df['time_diff'].sum()
    return total_active_time / 60  # Retourner en minutes

# Fonction pour calculer la distance totale
def calculate_total_distance(df):
    return df['distance'].iloc[-1] / 1000  # Conversion en km

# Fonction pour filtrer les fichiers en fonction des dates
def filter_by_date(df, start_date, end_date):
    mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
    return df[mask].copy()  # Créer une copie explicite

# Fonction pour calculer le temps passé dans chaque zone de fréquence cardiaque
def calculate_heart_rate_zones(df):
    if 'heart_rate' not in df or 'timestamp' not in df:
        return {}  # Retourne un dictionnaire vide si les colonnes sont manquantes

    # Ajouter une colonne 'zone' pour chaque enregistrement de fréquence cardiaque
    df['zone'] = df['heart_rate'].apply(determine_zone)

    # Calculer la durée de chaque enregistrement en secondes
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds().fillna(0)

    # Calculer le temps dans chaque zone
    time_in_zones = df.groupby('zone')['time_diff'].sum() / 60  # Conversion en minutes

    return time_in_zones.to_dict()  # Retourner sous forme de dictionnaire

# Fonction pour calculer la distance totale par semaine
def calculate_weekly_distance(activities):
    # Convertir la liste d'activités en DataFrame
    activities_df = pd.DataFrame(activities)
    activities_df['date'] = pd.to_datetime(activities_df['date'])
    
    # Extraire la semaine et l'année
    activities_df['week'] = activities_df['date'].dt.isocalendar().week
    activities_df['year'] = activities_df['date'].dt.year
    
    # Calculer la distance totale par semaine
    weekly_distance = activities_df.groupby(['year', 'week'])['distance (km)'].sum().reset_index()
    return weekly_distance

# Interface Streamlit
st.title("Analyse des Séances de Course à Pied")

# Onglets pour les différentes sections
tab1, tab2, tab3, tab4 = st.tabs(["Fréquence Cardiaque", "Allure", "Activités", "Évolution de la Distance"])

# Sélection de la plage de dates avec des clés uniques
start_date = st.date_input("Sélectionnez la date de début", pd.to_datetime("2024-10-01"), key="start_date_input")
end_date = st.date_input("Sélectionnez la date de fin", pd.to_datetime("2024-10-15"), key="end_date_input")

# Liste pour stocker les informations sur les activités
activities = []

# Initialiser les variables pour stocker les distances et temps
total_distance = 0
total_time = 0

# Ensemble pour éviter les doublons
activity_dates_set = set()

# Variables pour stocker les données de fréquence cardiaque
heart_rate_data = []

# Vérification des fichiers .zip et extraction
process_fit_files(folder_path, extracted_folder)

# Charger tous les fichiers .csv
csv_files = [f for f in os.listdir(extracted_folder) if f.endswith('.csv')]

for csv_file in csv_files:
    csvfile_path = os.path.join(extracted_folder, csv_file)
    
    # Charger le fichier .csv
    df = pd.read_csv(csvfile_path)

    # Convertir la colonne timestamp en datetime
    df.loc[:, 'timestamp'] = pd.to_datetime(df['timestamp'])

    # Filtrer les données par la plage de dates
    df_filtered = filter_by_date(df, pd.to_datetime(start_date), pd.to_datetime(end_date))

    if not df_filtered.empty:
        activity_date = df_filtered['timestamp'].iloc[0].date()

        distance = calculate_total_distance(df_filtered)
        active_time = calculate_active_time(df_filtered)

        if activity_date not in activity_dates_set:
            activities.append({
                'date': activity_date,
                'duration (minutes)': active_time,
                'distance (km)': distance
            })
            activity_dates_set.add(activity_date)

            total_distance += distance
            total_time += active_time

            hr_df = df_filtered[['timestamp', 'heart_rate']].copy()
            hr_df.loc[:, 'time_diff'] = hr_df['timestamp'].diff().dt.total_seconds().fillna(0) / 60  # Utiliser .loc ici
            heart_rate_data.append(hr_df)

# Nettoyage du dossier après traitement
cleanup_folder(extracted_folder)

# Calcul de l'allure moyenne
average_pace_min_per_km = (total_time / total_distance) if total_distance > 0 else 0  # en minutes par km

# Affichage des résultats dans l'onglet "Fréquence Cardiaque"
with tab1:
    st.write("Pourcentage du temps passé dans chaque zone de fréquence cardiaque :")
    time_in_zones_totals = {}  # Dictionnaire pour stocker les temps totaux par zone

    for hr_df in heart_rate_data:
        time_in_zones = calculate_heart_rate_zones(hr_df)
        
        # Additionner les temps dans les zones
        for zone, time in time_in_zones.items():
            if zone in time_in_zones_totals:
                time_in_zones_totals[zone] += time
            else:
                time_in_zones_totals[zone] = time

    # Créer un DataFrame à partir du dictionnaire
    time_in_zones_df = pd.Series(time_in_zones_totals)

    if not time_in_zones_df.empty:
        fig, ax = plt.subplots()
        time_in_zones_df.plot(kind='bar', ax=ax)
        ax.set_title('Temps passé dans chaque zone de fréquence cardiaque')
        ax.set_ylabel('Temps (minutes)')
        ax.set_xlabel('Zones de Fréquence Cardiaque')
        st.pyplot(fig)
    else:
        st.write("Aucune donnée disponible pour les zones de fréquence cardiaque.")

# Affichage des résultats dans l'onglet "Allure"
with tab2:
    st.write(f"Distance totale : {total_distance:.2f} km")
    st.write(f"Allure moyenne : {average_pace_min_per_km:.2f} min/km" if average_pace_min_per_km > 0 else "Allure non calculable.")

# Affichage des détails de chaque activité dans l'onglet "Activités"
with tab3:
    if activities:
        activities_df = pd.DataFrame(activities)
        activities_df['date'] = pd.to_datetime(activities_df['date'])
        activities_df['date'] = activities_df['date'].dt.strftime('%Y-%m-%d')  # Format de la date
        st.write("### Détails des Activités")
        st.write(activities_df)
    else:
        st.write("Aucune activité trouvée pour la période sélectionnée.")

# Affichage de l'évolution de la distance dans l'onglet "Évolution de la Distance"
with tab4:
    if activities:
        weekly_distance = calculate_weekly_distance(activities)
        
        # Création du graphique
        fig, ax = plt.subplots()
        ax.plot(weekly_distance['week'].astype(str) + '-' + weekly_distance['year'].astype(str), weekly_distance['distance (km)'], marker='o')
        ax.set_title('Évolution de la Distance Totale par Semaine')
        ax.set_xlabel('Semaine - Année')
        ax.set_ylabel('Distance Totale (km)')
        ax.set_xticks(range(len(weekly_distance)))
        ax.set_xticklabels(weekly_distance['week'].astype(str) + '-' + weekly_distance['year'].astype(str), rotation=45)
        st.pyplot(fig)
    else:
        st.write("Aucune activité trouvée pour la période sélectionnée.")
