import os
import zipfile
import pandas as pd
from fitparse import FitFile

def extract_fit_files_from_zip(zip_folder, extracted_folder):
    """
    Extrait les fichiers .fit de tous les fichiers .zip dans le dossier spécifié.
    """
    if not os.path.exists(extracted_folder):
        os.makedirs(extracted_folder)

    zip_files = [f for f in os.listdir(zip_folder) if f.endswith('.zip')]

    for zip_file in zip_files:
        with zipfile.ZipFile(os.path.join(zip_folder, zip_file), 'r') as z:
            z.extractall(extracted_folder)

def extract_and_save_fit_data(fitfile_path, csvfile_path):
    """
    Extrait les données d'un fichier .fit et les sauvegarde en .csv.
    """
    fitfile = FitFile(fitfile_path)
    data = []

    for record in fitfile.get_messages('record'):
        record_data = {}
        for field in record.fields:
            record_data[field.name] = field.value
        data.append(record_data)

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.to_csv(csvfile_path, index=False)  # Sauvegarder en .csv

def process_fit_files(folder_path, extracted_folder):
    """
    Traite les fichiers .fit extraits pour créer des fichiers .csv.
    """
    extract_fit_files_from_zip(folder_path, extracted_folder)
    fit_files = [f for f in os.listdir(extracted_folder) if f.endswith('.fit')]

    for fitfile in fit_files:
        fitfile_path = os.path.join(extracted_folder, fitfile)
        csvfile_path = os.path.splitext(fitfile_path)[0] + '.csv'  # Création du nom du fichier .csv

        # Vérifier si le fichier .csv existe déjà
        if not os.path.exists(csvfile_path):
            extract_and_save_fit_data(fitfile_path, csvfile_path)  # Extraire et sauvegarder si le fichier n'existe pas
