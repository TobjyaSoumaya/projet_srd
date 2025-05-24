"""
Simulateur de capteur de pression atmosphérique pour le système de gestion de climatisation intelligent.
Envoie périodiquement des données de pression simulées au serveur central via XML-RPC.
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

def simuler_pression(piece_id: str):
    """
    Simule un capteur de pression atmosphérique qui envoie périodiquement
    des données au serveur central
    
    Args:
        piece_id: Identifiant de la pièce où le capteur est installé
    """
    logger.info(f"Démarrage du simulateur de capteur de pression pour la pièce: {piece_id}")
    
    # Établir la connexion avec le serveur RPC
    proxy = xmlrpc.client.ServerProxy(SERVEUR_RPC_URL)
    
    # Pression initiale entre 1000 et 1025 hPa (hectopascals)
    pression = random.uniform(1000.0, 1025.0)
    
    # Simulation en continu
    while True:
        try:
            # Variation aléatoire légère de la pression (-0.5 à +0.5 hPa)
            pression += random.uniform(-0.5, 0.5)
            # Garder la pression dans une plage réaliste
            pression = max(min(pression, 1040.0), 975.0)
            
            # Envoyer la donnée au serveur RPC
            success = proxy.enregistrer_donnees_capteur(
                piece_id,        # ID de la pièce
                "pression",      # Type de capteur
                round(pression, 1),  # Valeur arrondie à 1 décimale
                "hPa"            # Unité de mesure
            )
            
            if success:
                logger.info(f"Pression envoyée pour {piece_id}: {round(pression, 1)} hPa")
            else:
                logger.warning(f"Échec de l'envoi de la pression pour {piece_id}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la pression: {e}")
        
        # Attendre avant le prochain envoi (entre 5 et 7 secondes)
        time.sleep(random.uniform(5.0, 6.0))

if __name__ == "__main__":
    # Vérifier si l'ID de la pièce est fourni en argument
    if len(sys.argv) < 2:
        print("Usage: python simulateur_capteur_pression.py <id_piece>")
        sys.exit(1)
    
    piece_id = sys.argv[1]
    simuler_pression(piece_id)
