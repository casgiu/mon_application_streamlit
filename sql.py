import sqlite3

# Connexion à la base de données (ou création si elle n'existe pas)
conn = sqlite3.connect('heartrate.db')
cursor = conn.cursor()

# Créer une table (si elle n'existe pas déjà)
cursor.execute('''
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    age INTEGER
)
''')

# Insertion de données
cursor.execute('''
INSERT INTO utilisateurs (nom, age,vma)
VALUES ('Paul-Auguste', 38, 14), ('Leana', 8, 10)
''')

# Sauvegarde des changements
conn.commit()

# Récupérer les données
cursor.execute('SELECT * FROM utilisateurs')
rows = cursor.fetchall()

for row in rows:
    print(row)

# Fermer la connexion
conn.close()
