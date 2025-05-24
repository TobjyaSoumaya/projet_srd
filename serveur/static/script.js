/**
 * script.js - Script principal pour l'interface utilisateur du système de gestion de climatisation
 * Gère la connexion aux API, l'affichage des données et les interactions utilisateur
 */

document.addEventListener('DOMContentLoaded', () => {
    // Éléments DOM
    const roomsContainer = document.getElementById('rooms-container');
    const roomCardTemplate = document.getElementById('room-card-template');
    
    // État local des pièces (pour comparer les mises à jour)
    let currentRooms = {};
    
    /**
     * Formate une valeur numérique avec son unité
     */
    function formatValue(value, unit) {
        if (value === null || value === undefined) return 'N/A';
        return `${parseFloat(value).toFixed(1)}${unit}`;
    }
    
    /**
     * Formate une date pour l'affichage
     */
    function formatDate(timestamp) {
        const date = new Date(timestamp * 1000);
        return date.toLocaleTimeString();
    }
    
    /**
     * Crée ou met à jour une carte pour une pièce
     */
    function updateRoomCard(roomId, roomData) {
        // Vérifier si la carte existe déjà
        let roomCard = document.querySelector(`.room-card[data-room-id="${roomId}"]`);
        
        // Si la carte n'existe pas, créer une nouvelle à partir du template
        if (!roomCard) {
            // Cloner le template
            const template = roomCardTemplate.content.cloneNode(true);
            roomCard = template.querySelector('.room-card');
            
            // Définir l'ID de la pièce
            roomCard.setAttribute('data-room-id', roomId);
            
            // Définir le nom de la pièce (en capitalisant la première lettre)
            const roomName = roomCard.querySelector('.room-name');
            roomName.textContent = roomId.charAt(0).toUpperCase() + roomId.slice(1);
            
            // Ajouter la carte au conteneur
            roomsContainer.appendChild(roomCard);
            
            // Ajouter les écouteurs d'événements pour les contrôles
            setupEventListeners(roomCard, roomId);
        }
        
        // Mettre à jour les données affichées
        
        // État de la climatisation
        const statusText = roomCard.querySelector('.status-text');
        if (roomData.climatisation_active) {
            roomCard.classList.add('ac-on');
            roomCard.classList.remove('ac-off');
            statusText.textContent = 'Climatisation active';
        } else {
            roomCard.classList.add('ac-off');
            roomCard.classList.remove('ac-on');
            statusText.textContent = 'Climatisation inactive';
        }
        
        // Température
        const tempValue = roomCard.querySelector('.temperature-value');
        if (roomData.temperature) {
            tempValue.textContent = formatValue(roomData.temperature.valeur, roomData.temperature.unite);
        } else {
            tempValue.textContent = 'N/A';
        }
        
        // Humidité
        const humValue = roomCard.querySelector('.humidity-value');
        if (roomData.humidite) {
            humValue.textContent = formatValue(roomData.humidite.valeur, roomData.humidite.unite);
        } else {
            humValue.textContent = 'N/A';
        }
        
        // Pression (optionnelle)
        const pressureRow = roomCard.querySelector('.pressure-row');
        const pressureValue = roomCard.querySelector('.pressure-value');
        if (roomData.pression) {
            pressureRow.style.display = 'flex';
            pressureValue.textContent = formatValue(roomData.pression.valeur, roomData.pression.unite);
        } else {
            pressureRow.style.display = 'none';
        }
        
        // Température cible
        const targetTempValue = roomCard.querySelector('.target-temp-value');
        targetTempValue.textContent = formatValue(roomData.temperature_cible, '°C');
        
        // États des interrupteurs
        const acToggle = roomCard.querySelector('.ac-toggle');
        acToggle.checked = roomData.climatisation_active;
        acToggle.disabled = roomData.mode_automatique;
        
        const autoToggle = roomCard.querySelector('.auto-toggle');
        autoToggle.checked = roomData.mode_automatique;
        
        // Dernière mise à jour
        const updateTime = roomCard.querySelector('.update-time');
        const latestTimestamp = getLatestTimestamp(roomData);
        if (latestTimestamp) {
            updateTime.textContent = formatDate(latestTimestamp);
        } else {
            updateTime.textContent = 'Jamais';
        }
    }
    
    /**
     * Obtient le timestamp le plus récent parmi les capteurs
     */
    function getLatestTimestamp(roomData) {
        let latest = 0;
        const sources = ['temperature', 'humidite', 'pression'];
        
        for (const source of sources) {
            if (roomData[source] && roomData[source].timestamp > latest) {
                latest = roomData[source].timestamp;
            }
        }
        
        return latest || null;
    }
    
    /**
     * Configure les écouteurs d'événements pour les contrôles d'une carte de pièce
     */
    function setupEventListeners(roomCard, roomId) {
        // Contrôle de la température cible
        const plusBtn = roomCard.querySelector('.temp-plus');
        const minusBtn = roomCard.querySelector('.temp-minus');
        const targetTempValue = roomCard.querySelector('.target-temp-value');
        
        plusBtn.addEventListener('click', () => {
            const currentTemp = parseFloat(targetTempValue.textContent);
            const newTemp = Math.min(currentTemp + 0.5, 30.0);
            updateTargetTemperature(roomId, newTemp);
        });
        
        minusBtn.addEventListener('click', () => {
            const currentTemp = parseFloat(targetTempValue.textContent);
            const newTemp = Math.max(currentTemp - 0.5, 15.0);
            updateTargetTemperature(roomId, newTemp);
        });
        
        // Interrupteur de climatisation
        const acToggle = roomCard.querySelector('.ac-toggle');
        acToggle.addEventListener('change', () => {
            updateACState(roomId, acToggle.checked);
        });
        
        // Interrupteur de mode automatique
        const autoToggle = roomCard.querySelector('.auto-toggle');
        autoToggle.addEventListener('change', () => {
            updateAutoMode(roomId, autoToggle.checked);
        });
    }
    
    /**
     * Envoie la température cible au serveur
     */
    async function updateTargetTemperature(roomId, temperature) {
        try {
            const response = await fetch(`/api/pieces/${roomId}/temperature-cible`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ temperature })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.erreur || 'Erreur lors de la mise à jour de la température cible');
            }
            
            // Pas besoin de mettre à jour l'interface ici, elle sera mise à jour automatiquement
            // via les événements SSE
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la mise à jour de la température cible: ' + error.message);
        }
    }
    
    /**
     * Envoie l'état de la climatisation au serveur
     */
    async function updateACState(roomId, active) {
        try {
            const response = await fetch(`/api/pieces/${roomId}/climatisation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ active })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.erreur || 'Erreur lors de la mise à jour de l\'état de la climatisation');
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la mise à jour de l\'état de la climatisation: ' + error.message);
            
            // Restaurer l'état précédent de l'interrupteur en cas d'erreur
            const roomCard = document.querySelector(`.room-card[data-room-id="${roomId}"]`);
            if (roomCard) {
                const acToggle = roomCard.querySelector('.ac-toggle');
                acToggle.checked = !active;
            }
        }
    }
    
    /**
     * Envoie le mode automatique au serveur
     */
    async function updateAutoMode(roomId, auto) {
        try {
            const response = await fetch(`/api/pieces/${roomId}/mode-automatique`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ auto })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.erreur || 'Erreur lors de la mise à jour du mode automatique');
            }
            
            // Si le mode automatique est activé, désactiver l'interrupteur de climatisation
            const roomCard = document.querySelector(`.room-card[data-room-id="${roomId}"]`);
            if (roomCard) {
                const acToggle = roomCard.querySelector('.ac-toggle');
                acToggle.disabled = auto;
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la mise à jour du mode automatique: ' + error.message);
            
            // Restaurer l'état précédent de l'interrupteur en cas d'erreur
            const roomCard = document.querySelector(`.room-card[data-room-id="${roomId}"]`);
            if (roomCard) {
                const autoToggle = roomCard.querySelector('.auto-toggle');
                autoToggle.checked = !auto;
            }
        }
    }
    
    /**
     * Initialise les connexions aux API
     */
    function init() {
        // Requête initiale pour obtenir l'état actuel
        fetch('/api/pieces')
            .then(response => response.json())
            .then(data => {
                // Supprimer le message de chargement
                const loading = roomsContainer.querySelector('.loading');
                if (loading) {
                    loading.remove();
                }
                
                // Mettre à jour l'interface avec les données reçues
                currentRooms = data;
                for (const [roomId, roomData] of Object.entries(data)) {
                    updateRoomCard(roomId, roomData);
                }
            })
            .catch(error => {
                console.error('Erreur lors du chargement initial:', error);
                roomsContainer.innerHTML = '<div class="error">Erreur lors du chargement des données. Veuillez rafraîchir la page.</div>';
            });
        
        // Configurer le streaming d'événements pour les mises à jour en temps réel
        const eventSource = new EventSource('/api/stream');
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            // Mettre à jour l'interface avec les nouvelles données
            for (const [roomId, roomData] of Object.entries(data)) {
                updateRoomCard(roomId, roomData);
            }
            
            // Mettre à jour l'état local
            currentRooms = data;
        };
        
        eventSource.onerror = function(error) {
            console.error('Erreur de la connexion au flux d\'événements:', error);
            // Tentative de reconnexion automatique après 5 secondes
            setTimeout(() => {
                console.log('Tentative de reconnexion au flux d\'événements...');
                eventSource.close();
                init();
            }, 5000);
        };
    }
    
    // Démarrer l'application
    init();
});
