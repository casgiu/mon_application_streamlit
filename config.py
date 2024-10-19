import os
import zipfile

# Chemins des dossiers
folder_path = '/Users/paulauguste/heartrate'
extracted_folder = '//Users/paulauguste/heartrate/extrait'

# Fonction pour extraire les fichiers .fit d'un fichier .zip
def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

# Fonction pour obtenir tous les fichiers .fit après extraction
def get_fit_files_from_zip(folder_path, extracted_folder):
    fit_files = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.zip'):
            zip_path = os.path.join(folder_path, filename)
            extract_zip(zip_path, extracted_folder)

            for extracted_filename in os.listdir(extracted_folder):
                if extracted_filename.endswith('.fit'):
                    fit_files.append(os.path.join(extracted_folder, extracted_filename))

    return fit_files

# Fonction pour nettoyer le dossier après extraction
def cleanup_folder(extracted_folder):
    for extracted_filename in os.listdir(extracted_folder):
        os.remove(os.path.join(extracted_folder, extracted_filename))
