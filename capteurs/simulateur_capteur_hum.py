"""
Simulateur de capteur d'humidité pour le système de gestion de climatisation intelligent.
Envoie périodiquement des données d'humidité simulées au serveur central via XML-RPC.
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

def simuler_humidite(piece_id: str):
    """
    Simule un capteur d'humidité SHT31 ou DHT22 qui envoie périodiquement
    des données au serveur central
    
    Args:
        piece_id: Identifiant de la pièce où le capteur est installé
    """
    logger.info(f"Démarrage du simulateur de capteur d'humidité pour la pièce: {piece_id}")
    
    # Établir la connexion avec le serveur RPC
    proxy = xmlrpc.client.ServerProxy(SERVEUR_RPC_URL)
    
    # Humidité initiale entre 40% et 60%
    humidite = random.uniform(40.0, 60.0)
    
    # Simulation en continu
    while True:
        try:
            # Variation aléatoire légère de l'humidité (-1% à +1%)
            humidite += random.uniform(-1.0, 1.0)
            # Garder l'humidité dans une plage réaliste
            humidite = max(min(humidite, 80.0), 20.0)
            
            # Envoyer la donnée au serveur RPC
            success = proxy.enregistrer_donnees_capteur(
                piece_id,        # ID de la pièce
                "humidite",      # Type de capteur
                round(humidite, 1),  # Valeur arrondie à 1 décimale
                "%"              # Unité de mesure
            )
            
            if success:
                logger.info(f"Humidité envoyée pour {piece_id}: {round(humidite, 1)}%")
            else:
                logger.warning(f"Échec de l'envoi de l'humidité pour {piece_id}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'humidité: {e}")
        
        # Attendre avant le prochain envoi (entre 3 et 5 secondes)
        time.sleep(random.uniform(20.0, 30.0))

if __name__ == "__main__":
    # Vérifier si l'ID de la pièce est fourni en argument
    if len(sys.argv) < 2:
        print("Usage: python simulateur_capteur_hum.py <id_piece>")
        sys.exit(1)
    
    piece_id = sys.argv[1]
    simuler_humidite(piece_id)
