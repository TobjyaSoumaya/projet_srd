"""
Gestionnaire de capteurs intégré pour le système de gestion de climatisation intelligent.
Permet de démarrer et arrêter les simulateurs de capteurs directement depuis l'interface web.
"""
import threading
import time
import random
import xmlrpc.client
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Configuration du client RPC
SERVEUR_RPC_URL = "http://localhost:8000/RPC2"

class SimulateurCapteur:
    """Classe de base pour les simulateurs de capteurs"""
    
    def __init__(self, piece_id: str, type_capteur: str):
        self.piece_id = piece_id
        self.type_capteur = type_capteur
        self.actif = False
        self.thread = None
        self.proxy = None
        
    def demarrer(self):
        """Démarre la simulation du capteur"""
        if not self.actif:
            self.actif = True
            self.thread = threading.Thread(target=self._simuler, daemon=True)
            self.thread.start()
            logger.info(f"Capteur {self.type_capteur} démarré pour la pièce {self.piece_id}")
    
    def arreter(self):
        """Arrête la simulation du capteur"""
        self.actif = False
        if self.thread:
            self.thread = None
        logger.info(f"Capteur {self.type_capteur} arrêté pour la pièce {self.piece_id}")
    
    def _simuler(self):
        """Méthode abstraite à implémenter par les sous-classes"""
        pass

class SimulateurTemperature(SimulateurCapteur):
    """Simulateur de capteur de température"""
    
    def __init__(self, piece_id: str):
        super().__init__(piece_id, "temperature")
        self.temperature = random.uniform(18.0, 25.0)
        self.mode_refroidissement = False
        self.temps_refroidissement = 0
        self.duree_maximale_refroidissement = 60
    
    def _simuler(self):
        """Simule le capteur de température"""
        self.proxy = xmlrpc.client.ServerProxy(SERVEUR_RPC_URL)
        
        while self.actif:
            try:
                # Récupérer l'état actuel de la pièce
                try:
                    pieces = self.proxy.obtenir_donnees_pieces()
                    
                    if self.piece_id in pieces:
                        piece_data = pieces[self.piece_id]
                        climatisation_active = piece_data.get('climatisation_active', False)
                        temperature_cible = piece_data.get('temperature_cible', 21.0)
                        
                        if climatisation_active:
                            self.mode_refroidissement = True
                            self.temps_refroidissement = 0
                        
                        if self.mode_refroidissement:
                            difference = self.temperature - temperature_cible
                            vitesse_refroidissement = min(0.5, abs(difference) * 0.1)
                            
                            if difference > 0:
                                self.temperature -= vitesse_refroidissement
                            elif difference < -0.2:
                                self.temperature += vitesse_refroidissement * 0.5
                            
                            self.temps_refroidissement += random.uniform(2.0, 4.0)
                            
                            if (self.temps_refroidissement >= self.duree_maximale_refroidissement or
                                    abs(self.temperature - temperature_cible) < 0.3):
                                self.mode_refroidissement = False
                        else:
                            self.temperature += random.uniform(-0.2, 0.2)
                
                except Exception as e:
                    logger.warning(f"Impossible de récupérer les données de la pièce: {e}")
                    self.temperature += random.uniform(-0.2, 0.2)
                
                # Garder la température dans une plage réaliste
                self.temperature = max(min(self.temperature, 30.0), 15.0)
                
                # Envoyer la donnée au serveur RPC
                success = self.proxy.enregistrer_donnees_capteur(
                    self.piece_id,
                    "temperature",
                    round(self.temperature, 1),
                    "°C"
                )
                
                if success:
                    mode_info = "Mode refroidissement" if self.mode_refroidissement else "Mode aléatoire"
                    logger.info(f"Température envoyée pour {self.piece_id}: {round(self.temperature, 1)}°C ({mode_info})")
                else:
                    logger.warning(f"Échec de l'envoi de la température pour {self.piece_id}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la température: {e}")
            
            time.sleep(random.uniform(2.0, 4.0))

class SimulateurHumidite(SimulateurCapteur):
    """Simulateur de capteur d'humidité"""
    
    def __init__(self, piece_id: str):
        super().__init__(piece_id, "humidite")
        self.humidite = random.uniform(40.0, 60.0)
    
    def _simuler(self):
        """Simule le capteur d'humidité"""
        self.proxy = xmlrpc.client.ServerProxy(SERVEUR_RPC_URL)
        
        while self.actif:
            try:
                # Variation aléatoire légère de l'humidité
                self.humidite += random.uniform(-1.0, 1.0)
                self.humidite = max(min(self.humidite, 80.0), 20.0)
                
                # Envoyer la donnée au serveur RPC
                success = self.proxy.enregistrer_donnees_capteur(
                    self.piece_id,
                    "humidite",
                    round(self.humidite, 1),
                    "%"
                )
                
                if success:
                    logger.info(f"Humidité envoyée pour {self.piece_id}: {round(self.humidite, 1)}%")
                else:
                    logger.warning(f"Échec de l'envoi de l'humidité pour {self.piece_id}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'humidité: {e}")
            
            time.sleep(random.uniform(20.0, 30.0))

class SimulateurPression(SimulateurCapteur):
    """Simulateur de capteur de pression"""
    
    def __init__(self, piece_id: str):
        super().__init__(piece_id, "pression")
        self.pression = random.uniform(1000.0, 1025.0)
    
    def _simuler(self):
        """Simule le capteur de pression"""
        self.proxy = xmlrpc.client.ServerProxy(SERVEUR_RPC_URL)
        
        while self.actif:
            try:
                # Variation aléatoire légère de la pression
                self.pression += random.uniform(-0.5, 0.5)
                self.pression = max(min(self.pression, 1040.0), 975.0)
                
                # Envoyer la donnée au serveur RPC
                success = self.proxy.enregistrer_donnees_capteur(
                    self.piece_id,
                    "pression",
                    round(self.pression, 1),
                    "hPa"
                )
                
                if success:
                    logger.info(f"Pression envoyée pour {self.piece_id}: {round(self.pression, 1)} hPa")
                else:
                    logger.warning(f"Échec de l'envoi de la pression pour {self.piece_id}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la pression: {e}")
            
            time.sleep(random.uniform(5.0, 6.0))

class GestionnaireCapteurs:
    """Gestionnaire principal des capteurs"""
    
    def __init__(self):
        self.capteurs: Dict[str, Dict[str, SimulateurCapteur]] = {}
        # Dictionnaire structure: {piece_id: {type_capteur: simulateur}}
    
    def ajouter_piece(self, piece_id: str):
        """Ajoute une nouvelle pièce avec ses capteurs"""
        if piece_id not in self.capteurs:
            self.capteurs[piece_id] = {
                'temperature': SimulateurTemperature(piece_id),
                'humidite': SimulateurHumidite(piece_id),
                'pression': SimulateurPression(piece_id)
            }
            logger.info(f"Pièce {piece_id} ajoutée avec ses capteurs")
    
    def demarrer_capteurs_piece(self, piece_id: str):
        """Démarre tous les capteurs d'une pièce"""
        if piece_id in self.capteurs:
            for capteur in self.capteurs[piece_id].values():
                capteur.demarrer()
            logger.info(f"Capteurs démarrés pour la pièce {piece_id}")
    
    def arreter_capteurs_piece(self, piece_id: str):
        """Arrête tous les capteurs d'une pièce"""
        if piece_id in self.capteurs:
            for capteur in self.capteurs[piece_id].values():
                capteur.arreter()
            logger.info(f"Capteurs arrêtés pour la pièce {piece_id}")
    
    def demarrer_capteur(self, piece_id: str, type_capteur: str):
        """Démarre un capteur spécifique"""
        if piece_id in self.capteurs and type_capteur in self.capteurs[piece_id]:
            self.capteurs[piece_id][type_capteur].demarrer()
    
    def arreter_capteur(self, piece_id: str, type_capteur: str):
        """Arrête un capteur spécifique"""
        if piece_id in self.capteurs and type_capteur in self.capteurs[piece_id]:
            self.capteurs[piece_id][type_capteur].arreter()
    
    def obtenir_etat_capteurs(self):
        """Retourne l'état de tous les capteurs"""
        etat = {}
        for piece_id, capteurs_piece in self.capteurs.items():
            etat[piece_id] = {}
            for type_capteur, capteur in capteurs_piece.items():
                etat[piece_id][type_capteur] = {
                    'actif': capteur.actif,
                    'type': type_capteur
                }
        return etat
    
    def supprimer_piece(self, piece_id: str):
        """Supprime une pièce et arrête tous ses capteurs"""
        if piece_id in self.capteurs:
            self.arreter_capteurs_piece(piece_id)
            del self.capteurs[piece_id]
            logger.info(f"Pièce {piece_id} supprimée")
    
    def obtenir_pieces_disponibles(self) -> List[str]:
        """Retourne la liste des pièces disponibles"""
        return list(self.capteurs.keys())

# Instance globale du gestionnaire
gestionnaire_capteurs = GestionnaireCapteurs()