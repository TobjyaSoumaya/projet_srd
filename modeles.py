"""
Module pour la gestion des données des pièces et de la climatisation.
Contient les classes et structures de données utilisées par le serveur central.
"""
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class DonneesCapteur:
    """Classe pour stocker les données d'un capteur"""
    valeur: float
    timestamp: float = field(default_factory=time.time)
    unite: str = ""


@dataclass
class Piece:
    """Classe représentant une pièce avec ses capteurs et son état de climatisation"""
    id: str
    temperature: Optional[DonneesCapteur] = None
    humidite: Optional[DonneesCapteur] = None
    pression: Optional[DonneesCapteur] = None
    temperature_cible: float = 21.0  # Température cible par défaut
    climatisation_active: bool = False
    mode_automatique: bool = True  # Mode automatique activé par défaut


class GestionnairePieces:
    """Classe pour gérer l'ensemble des pièces du système"""
    def __init__(self):
        self.pieces: Dict[str, Piece] = {}
    
    def obtenir_piece(self, id_piece: str) -> Piece:
        """Obtient une pièce ou en crée une nouvelle si elle n'existe pas"""
        if id_piece not in self.pieces:
            self.pieces[id_piece] = Piece(id=id_piece)
        return self.pieces[id_piece]
    
    def enregistrer_donnee_capteur(self, id_piece: str, type_capteur: str, valeur: float, unite: str) -> None:
        """Enregistre la donnée d'un capteur pour une pièce spécifique"""
        piece = self.obtenir_piece(id_piece)
        donnee = DonneesCapteur(valeur=valeur, unite=unite)
        
        if type_capteur == "temperature":
            piece.temperature = donnee
            self._verifier_ajustement_automatique(piece)
        elif type_capteur == "humidite":
            piece.humidite = donnee
        elif type_capteur == "pression":
            piece.pression = donnee
    
    def definir_temperature_cible(self, id_piece: str, temperature: float) -> None:
        """Définit la température cible pour une pièce"""
        piece = self.obtenir_piece(id_piece)
        piece.temperature_cible = temperature
        self._verifier_ajustement_automatique(piece)
    
    def definir_etat_climatisation(self, id_piece: str, active: bool) -> None:
        """Définit l'état de la climatisation pour une pièce"""
        piece = self.obtenir_piece(id_piece)
        piece.climatisation_active = active
    
    def definir_mode_automatique(self, id_piece: str, auto: bool) -> None:
        """Active ou désactive le mode automatique pour une pièce"""
        piece = self.obtenir_piece(id_piece)
        piece.mode_automatique = auto
        if auto:
            self._verifier_ajustement_automatique(piece)
    
    def _verifier_ajustement_automatique(self, piece: Piece) -> None:
        """Vérifie et ajuste l'état de la climatisation en mode automatique"""
        if not piece.mode_automatique or not piece.temperature:
            return
        
        # Logique d'ajustement automatique
        # Si la température actuelle est supérieure à la cible de plus de 0.5°C, activer la climatisation
        # Si la température actuelle est inférieure à la cible de plus de 0.5°C, désactiver la climatisation
        if piece.temperature.valeur > piece.temperature_cible + 0.5:
            piece.climatisation_active = True
        elif piece.temperature.valeur < piece.temperature_cible - 0.5:
            piece.climatisation_active = False
    
    def obtenir_toutes_pieces(self) -> Dict[str, Piece]:
        """Retourne toutes les pièces enregistrées"""
        return self.pieces
        
    def obtenir_donnees_pieces(self) -> Dict[str, Dict]:
        """Retourne les données des pièces dans un format sérialisable pour le RPC"""
        resultat = {}
        for id_piece, piece in self.pieces.items():
            resultat[id_piece] = {
                'id': piece.id,
                'temperature': {
                    'valeur': piece.temperature.valeur,
                    'unite': piece.temperature.unite,
                    'timestamp': piece.temperature.timestamp
                } if piece.temperature else None,
                'humidite': {
                    'valeur': piece.humidite.valeur,
                    'unite': piece.humidite.unite,
                    'timestamp': piece.humidite.timestamp
                } if piece.humidite else None,
                'pression': {
                    'valeur': piece.pression.valeur,
                    'unite': piece.pression.unite,
                    'timestamp': piece.pression.timestamp
                } if piece.pression else None,
                'temperature_cible': piece.temperature_cible,
                'climatisation_active': piece.climatisation_active,
                'mode_automatique': piece.mode_automatique
            }
        return resultat