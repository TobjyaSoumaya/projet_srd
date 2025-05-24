"""
Simulateur de capteur de température pour le système de gestion de climatisation intelligent.
Envoie périodiquement des données de température simulées au serveur central via XML-RPC.
"""
import sys
import time
import random
import xmlrpc.client
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration du client RPC
SERVEUR_RPC_URL = "http://localhost:8000/RPC2"

def simuler_temperature(piece_id: str):
    """
    Simule un capteur de température DS18B20 ou DHT22 qui envoie périodiquement
    des données au serveur central
    
    Args:
        piece_id: Identifiant de la pièce où le capteur est installé
    """
    logger.info(f"Démarrage du simulateur de capteur de température pour la pièce: {piece_id}")
    
    # Établir la connexion avec le serveur RPC
    proxy = xmlrpc.client.ServerProxy(SERVEUR_RPC_URL)
    
    # Température initiale entre 18 et 25 degrés Celsius
    temperature = random.uniform(18.0, 25.0)
    
    # Variables pour simuler l'effet de la climatisation
    mode_refroidissement = False
    temps_refroidissement = 0
    duree_maximale_refroidissement = 60  # 60 secondes (défini en secondes pour la simulation)
    
    # Simulation en continu
    while True:
        try:
            # Récupérer l'état actuel de la pièce
            try:
                # Obtenir les données actuelles de la pièce via l'API
                pieces = proxy.obtenir_donnees_pieces()
                
                if piece_id in pieces:
                    piece_data = pieces[piece_id]
                    
                    climatisation_active = piece_data.get('climatisation_active', False)
                    temperature_cible = piece_data.get('temperature_cible', 21.0)
                    
                    # Si la climatisation est active, simuler le refroidissement
                    if climatisation_active:
                        mode_refroidissement = True
                        temps_refroidissement = 0  # Réinitialiser le compteur
                    
                    # Ajuster la température en fonction de l'état de la climatisation
                    if mode_refroidissement:
                        # Quand la climatisation est active, la température tend vers la cible
                        difference = temperature - temperature_cible
                        
                        # La vitesse de refroidissement est proportionnelle à la différence
                        vitesse_refroidissement = min(0.5, abs(difference) * 0.1)
                        
                        if difference > 0:
                            # Refroidir (diminuer la température)
                            temperature -= vitesse_refroidissement
                        elif difference < -0.2:
                            # Réchauffer légèrement si trop froid
                            temperature += vitesse_refroidissement * 0.5
                        
                        # Incrémenter le temps de refroidissement
                        temps_refroidissement += random.uniform(2.0, 4.0)
                        
                        # Si le temps de refroidissement dépasse la durée maximale,
                        # ou si la température est proche de la cible, revenir au mode aléatoire
                        if (temps_refroidissement >= duree_maximale_refroidissement or
                                abs(temperature - temperature_cible) < 0.3):
                            mode_refroidissement = False
                    else:
                        # Variation aléatoire légère de la température (-0.2 à +0.2 degrés)
                        temperature += random.uniform(-0.2, 0.2)
                
            except Exception as e:
                logger.warning(f"Impossible de récupérer les données de la pièce: {e}")
                # Variation aléatoire par défaut si erreur
                temperature += random.uniform(-0.2, 0.2)
            
            # Garder la température dans une plage réaliste
            temperature = max(min(temperature, 30.0), 15.0)
            
            # Envoyer la donnée au serveur RPC
            success = proxy.enregistrer_donnees_capteur(
                piece_id,        # ID de la pièce
                "temperature",   # Type de capteur
                round(temperature, 1),  # Valeur arrondie à 1 décimale
                "°C"             # Unité de mesure
            )
            
            if success:
                mode_info = "Mode refroidissement" if mode_refroidissement else "Mode aléatoire"
                logger.info(f"Température envoyée pour {piece_id}: {round(temperature, 1)}°C ({mode_info})")
            else:
                logger.warning(f"Échec de l'envoi de la température pour {piece_id}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la température: {e}")
        
        # Attendre avant le prochain envoi (entre 2 et 4 secondes)
        time.sleep(random.uniform(2.0, 4.0))

if __name__ == "__main__":
    # Vérifier si l'ID de la pièce est fourni en argument
    if len(sys.argv) < 2:
        print("Usage: python simulateur_capteur_temp.py <id_piece>")
        sys.exit(1)
    
    piece_id = sys.argv[1]
    simuler_temperature(piece_id)