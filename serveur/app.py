"""
Serveur central pour le système de gestion de climatisation intelligent.
Combine un serveur XML-RPC pour recevoir les données des capteurs
et un serveur Flask pour servir l'interface web et les API REST.
Version modifiée avec gestion intégrée des capteurs.
"""
import threading
import xmlrpc.server
from xmlrpc.server import SimpleXMLRPCServer
from flask import Flask, render_template, jsonify, request, Response
from modeles import GestionnairePieces
from gestionnaire_capteurs import gestionnaire_capteurs
import logging
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation du gestionnaire de pièces (singleton)
gestionnaire_pieces = GestionnairePieces()

# Configuration du serveur XML-RPC
class RPCHandler:
    def enregistrer_donnees_capteur(self, id_piece, type_capteur, valeur, unite):
        """
        Méthode RPC pour l'enregistrement des données des capteurs
        """
        try:
            valeur = float(valeur)
            logger.info(f"Données reçues - Pièce: {id_piece}, Capteur: {type_capteur}, Valeur: {valeur} {unite}")
            gestionnaire_pieces.enregistrer_donnee_capteur(id_piece, type_capteur, valeur, unite)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des données: {e}")
            return False
    
    def obtenir_donnees_pieces(self):
        """
        Méthode RPC pour obtenir les données actuelles des pièces
        Permet aux simulateurs de connaître l'état de la climatisation
        """
        try:
            return gestionnaire_pieces.obtenir_donnees_pieces()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données des pièces: {e}")
            return {}

def demarrer_serveur_rpc():
    """
    Démarre le serveur XML-RPC dans un thread séparé
    """
    adresse_rpc = ('0.0.0.0', 8000)
    serveur = SimpleXMLRPCServer(adresse_rpc, allow_none=True, logRequests=False)
    serveur.register_instance(RPCHandler())
    logger.info(f"Serveur RPC démarré sur http://{adresse_rpc[0]}:{adresse_rpc[1]}/RPC2")
    serveur.serve_forever()

# Configuration du serveur Flask et des API REST
app = Flask(__name__)

@app.route('/')
def index():
    """
    Route principale qui sert l'interface utilisateur
    """
    return render_template('index.html')

@app.route('/api/pieces', methods=['GET'])
def api_pieces():
    """
    API pour obtenir toutes les pièces et leurs données actuelles
    """
    pieces = gestionnaire_pieces.obtenir_toutes_pieces()
    
    # Conversion en dictionnaire pour la sérialisation JSON
    resultat = {}
    for id_piece, piece in pieces.items():
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
    
    return jsonify(resultat)

@app.route('/api/pieces/<id_piece>/temperature-cible', methods=['POST'])
def api_definir_temperature_cible(id_piece):
    """
    API pour définir la température cible d'une pièce
    """
    data = request.json
    if 'temperature' not in data:
        return jsonify({'erreur': 'Température manquante'}), 400
    
    try:
        temperature = float(data['temperature'])
        gestionnaire_pieces.definir_temperature_cible(id_piece, temperature)
        return jsonify({'succes': True, 'temperature_cible': temperature})
    except ValueError:
        return jsonify({'erreur': 'Valeur de température invalide'}), 400

@app.route('/api/pieces/<id_piece>/climatisation', methods=['POST'])
def api_definir_etat_climatisation(id_piece):
    """
    API pour définir l'état de la climatisation d'une pièce
    """
    data = request.json
    if 'active' not in data:
        return jsonify({'erreur': 'État de climatisation manquant'}), 400
    
    try:
        active = bool(data['active'])
        gestionnaire_pieces.definir_etat_climatisation(id_piece, active)
        return jsonify({'succes': True, 'climatisation_active': active})
    except ValueError:
        return jsonify({'erreur': 'Valeur d\'état invalide'}), 400

@app.route('/api/pieces/<id_piece>/mode-automatique', methods=['POST'])
def api_definir_mode_automatique(id_piece):
    """
    API pour définir le mode automatique d'une pièce
    """
    data = request.json
    if 'auto' not in data:
        return jsonify({'erreur': 'Mode automatique manquant'}), 400
    
    try:
        auto = bool(data['auto'])
        gestionnaire_pieces.definir_mode_automatique(id_piece, auto)
        return jsonify({'succes': True, 'mode_automatique': auto})
    except ValueError:
        return jsonify({'erreur': 'Valeur de mode invalide'}), 400

# === NOUVELLES ROUTES POUR LA GESTION DES CAPTEURS ===

@app.route('/api/capteurs/pieces', methods=['GET'])
def api_obtenir_pieces_capteurs():
    """
    API pour obtenir la liste des pièces avec capteurs et leur état
    """
    pieces_capteurs = gestionnaire_capteurs.obtenir_pieces_disponibles()
    etat_capteurs = gestionnaire_capteurs.obtenir_etat_capteurs()
    
    return jsonify({
        'pieces': pieces_capteurs,
        'etat_capteurs': etat_capteurs
    })

@app.route('/api/capteurs/pieces', methods=['POST'])
def api_ajouter_piece_capteurs():
    """
    API pour ajouter une nouvelle pièce avec ses capteurs
    """
    data = request.json
    if 'nom_piece' not in data:
        return jsonify({'erreur': 'Nom de pièce manquant'}), 400
    
    nom_piece = data['nom_piece'].strip()
    if not nom_piece:
        return jsonify({'erreur': 'Nom de pièce vide'}), 400
    
    # Ajouter la pièce au gestionnaire de capteurs
    gestionnaire_capteurs.ajouter_piece(nom_piece)
    
    return jsonify({
        'succes': True,
        'message': f'Pièce "{nom_piece}" ajoutée avec succès',
        'piece_id': nom_piece
    })

@app.route('/api/capteurs/pieces/<piece_id>', methods=['DELETE'])
def api_supprimer_piece_capteurs(piece_id):
    """
    API pour supprimer une pièce et ses capteurs
    """
    gestionnaire_capteurs.supprimer_piece(piece_id)
    return jsonify({
        'succes': True,
        'message': f'Pièce "{piece_id}" supprimée avec succès'
    })

@app.route('/api/capteurs/pieces/<piece_id>/demarrer', methods=['POST'])
def api_demarrer_capteurs_piece(piece_id):
    """
    API pour démarrer les capteurs d'une pièce
    """
    gestionnaire_capteurs.demarrer_capteurs_piece(piece_id)
    return jsonify({
        'succes': True,
        'message': f'Capteurs démarrés pour la pièce "{piece_id}"'
    })

@app.route('/api/capteurs/pieces/<piece_id>/arreter', methods=['POST'])
def api_arreter_capteurs_piece(piece_id):
    """
    API pour arrêter les capteurs d'une pièce
    """
    gestionnaire_capteurs.arreter_capteurs_piece(piece_id)
    return jsonify({
        'succes': True,
        'message': f'Capteurs arrêtés pour la pièce "{piece_id}"'
    })

@app.route('/api/capteurs/pieces/<piece_id>/<type_capteur>/demarrer', methods=['POST'])
def api_demarrer_capteur(piece_id, type_capteur):
    """
    API pour démarrer un capteur spécifique
    """
    gestionnaire_capteurs.demarrer_capteur(piece_id, type_capteur)
    return jsonify({
        'succes': True,
        'message': f'Capteur {type_capteur} démarré pour la pièce "{piece_id}"'
    })

@app.route('/api/capteurs/pieces/<piece_id>/<type_capteur>/arreter', methods=['POST'])
def api_arreter_capteur(piece_id, type_capteur):
    """
    API pour arrêter un capteur spécifique
    """
    gestionnaire_capteurs.arreter_capteur(piece_id, type_capteur)
    return jsonify({
        'succes': True,
        'message': f'Capteur {type_capteur} arrêté pour la pièce "{piece_id}"'
    })

@app.route('/api/stream')
def stream():
    """
    API pour le streaming des mises à jour (Server-Sent Events)
    """
    def event_stream():
        last_data = {}
        while True:
            # Récupération des données des pièces
            pieces = gestionnaire_pieces.obtenir_toutes_pieces()
            
            # Conversion en dictionnaire pour la sérialisation
            current_data = {}
            for id_piece, piece in pieces.items():
                current_data[id_piece] = {
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
            
            # Envoyer uniquement si les données ont changé
            if current_data != last_data:
                last_data = current_data
                yield f"data: {json.dumps(current_data)}\n\n"
            
            # Attendre un peu avant la prochaine vérification
            import time
            time.sleep(1)
    
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    # Démarrage du serveur RPC dans un thread séparé
    thread_rpc = threading.Thread(target=demarrer_serveur_rpc, daemon=True)
    thread_rpc.start()
    
    # Démarrage du serveur Flask
    logger.info("Démarrage du serveur Flask sur http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)