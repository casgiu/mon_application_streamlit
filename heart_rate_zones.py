# Fonction pour déterminer la zone de fréquence cardiaque
def determine_zone(hr):
    if 120 < hr < 144:
        return 1
    elif 144 <= hr <= 157:
        return 2
    elif 158 <= hr <= 172:
        return 3
    elif 173 <= hr <= 186:
        return 4
    elif 187 <= hr <= 200:
        return 5
    else:
        return None
