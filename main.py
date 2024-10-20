import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import os
from config import folder_path, extracted_folder, cleanup_folder
from heart_rate_zones import determine_zone
from fonctions import (calculate_active_time, calculate_total_distance, 
                       filter_by_date, calculate_heart_rate_zones, 
                       calculate_weekly_distance, calculate_time_above_90_percent_vma, format_duration)
from data_extraction import process_fit_files
from datetime import datetime, timedelta
import plotly.graph_objects as go


# Interface Streamlit
st.title("Analyse des Séances de Course à Pied")

# Obtenir la date d'aujourd'hui
today = datetime.today()

# Initialiser le session state pour les dates si nécessaire
if 'start_date' not in st.session_state:
    st.session_state.start_date = today - timedelta(days=7)  # 7 jours avant aujourd'hui
if 'end_date' not in st.session_state:
    st.session_state.end_date = today  # Date d'aujourd'hui

# Créer des colonnes pour la sélection de dates et les boutons
col1, col2 = st.columns(2)

# Colonne 1: Sélection de la plage de dates
with col1:
    st.header("Sélectionnez une plage de dates")
    st.session_state.end_date = st.date_input("Date de fin", st.session_state.end_date, key="end_date_input")
    st.session_state.start_date = st.date_input("Date de début", st.session_state.start_date, key="start_date_input")

# Colonne 2: Boutons pour sélectionner la période
with col2:
    st.header("Sélectionnez une période")
    
    # Choisir la semaine en cours
    if st.button("Semaine en cours"):
        start_of_week = today - timedelta(days=today.weekday())  # Lundi de la semaine en cours
        end_of_week = start_of_week + timedelta(days=6)  # Dimanche de la semaine en cours
        st.session_state.start_date = start_of_week
        st.session_state.end_date = end_of_week

    # Choisir le mois en cours
    if st.button("Mois en cours"):
        st.session_state.start_date = today.replace(day=1)  # 1er jour du mois
        st.session_state.end_date = today  # Date d'aujourd'hui

    # Choisir "Depuis le début"
    if st.button("Depuis le début"):
        first_activity_date = pd.to_datetime("2024-01-01")  # Exemple de date (remplacez par votre logique)
        st.session_state.start_date = first_activity_date
        st.session_state.end_date = today

# Onglets pour les différentes sections
tab1, tab2, tab3, tab4 = st.tabs(["Fréquence Cardiaque", "Allure", "Activités", "Évolution de la Distance"])

# Liste pour stocker les informations sur les activités
activities = []
total_distance = 0
total_time = 0
activity_dates_set = set()
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
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Filtrer les données par la plage de dates
    df_filtered = filter_by_date(df, st.session_state.start_date, st.session_state.end_date)

    if not df_filtered.empty:
        activity_date = df_filtered['timestamp'].iloc[0].date()

        distance = calculate_total_distance(df_filtered)
        active_time = calculate_active_time(df_filtered)
        time_above_vma = calculate_time_above_90_percent_vma(df_filtered)

        if activity_date not in activity_dates_set:
            activities.append({
                'date': activity_date,
                'duration (minutes)': active_time,
                'distance (km)': distance,
                'Temps >= 90% VMA (minutes)': time_above_vma
            })
            activity_dates_set.add(activity_date)

            total_distance += distance
            total_time += active_time

            hr_df = df_filtered[['timestamp', 'heart_rate']].copy()
            hr_df['time_diff'] = hr_df['timestamp'].diff().dt.total_seconds().fillna(0) / 60
            heart_rate_data.append(hr_df)

# Nettoyage du dossier après traitement
cleanup_folder(extracted_folder)

# Calcul de l'allure moyenne
average_pace_min_per_km = (total_time / total_distance) if total_distance > 0 else 0

# Affichage des résultats dans l'onglet "Fréquence Cardiaque"
with tab1:
    st.write("Pourcentage du temps passé dans chaque zone de fréquence cardiaque :")
    time_in_zones_totals = {}

    # Calculer le temps passé dans chaque zone de fréquence cardiaque
    for hr_df in heart_rate_data:
        time_in_zones = calculate_heart_rate_zones(hr_df, determine_zone)
        
        for zone, time in time_in_zones.items():
            if zone in time_in_zones_totals:
                time_in_zones_totals[zone] += time
            else:
                time_in_zones_totals[zone] = time

    time_in_zones_df = pd.Series(time_in_zones_totals)

    if not time_in_zones_df.empty:
        # Appliquer la conversion min:sec aux durées
        formatted_durations = time_in_zones_df.apply(format_duration)

        # Créer le graphique Plotly
        fig = px.bar(
            time_in_zones_df,
            x=time_in_zones_df.index,
            y=time_in_zones_df.values,
            labels={'x': 'Zones de Fréquence Cardiaque', 'y': 'Temps (minutes)'},
            title='Temps passé dans chaque zone de fréquence cardiaque',
        )

        # Personnaliser les infos affichées au survol
        fig.update_traces(hovertemplate='Zone %{x}<br>Durée: %{customdata}<extra></extra>',
                          customdata=formatted_durations)

        # Afficher le graphique dans Streamlit
        st.plotly_chart(fig)
    else:
        st.write("Aucune donnée disponible pour les zones de fréquence cardiaque.")

# Affichage des résultats dans l'onglet "Allure"
with tab2:
    st.write(f"Distance totale : {total_distance:.2f} km")
    formatted_pace = format_duration(average_pace_min_per_km) if average_pace_min_per_km > 0 else "Non calculable"
    st.write(f"Allure moyenne : {formatted_pace} min/km")

# Affichage des détails de chaque activité dans l'onglet "Activités"
with tab3:
    if activities:
        activities_df = pd.DataFrame(activities)
        activities_df['date'] = pd.to_datetime(activities_df['date']).dt.strftime('%Y-%m-%d')
        activities_df['duration (minutes)'] = activities_df['duration (minutes)'].apply(format_duration)
        activities_df['Temps >= 90% VMA (minutes)'] = activities_df['Temps >= 90% VMA (minutes)'].apply(format_duration)
        st.write("### Détails des Activités")
        st.write(activities_df)
    else:
        st.write("Aucune activité trouvée pour la période sélectionnée.")

# Graphique de l'évolution de la distance
with tab4:
    if activities:
        weekly_distance = calculate_weekly_distance(activities)

        # Créer le graphique Plotly
        fig = go.Figure()

        # Ajouter une trace pour la distance hebdomadaire
        fig.add_trace(go.Scatter(
            x=weekly_distance['week'].astype(str) + '-' + weekly_distance['year'].astype(str),
            y=weekly_distance['distance (km)'],
            mode='lines+markers',
            marker=dict(size=8, color='blue'),
            line=dict(color='blue'),
            hovertemplate='Semaine %{x}<br>Distance: %{y} km<extra></extra>'
        ))

        # Définir les titres et les labels
        fig.update_layout(
            title='Évolution de la Distance Totale par Semaine',
            xaxis_title='Semaine - Année',
            yaxis_title='Distance Totale (km)',
            xaxis_tickangle=-45,
            template='plotly_white',
            hovermode='x'
        )

        # Afficher le graphique interactif dans Streamlit
        st.plotly_chart(fig)
    else:
        st.write("Aucune activité trouvée pour la période sélectionnée.")
