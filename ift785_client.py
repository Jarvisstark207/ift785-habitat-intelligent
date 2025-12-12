"""
Client MQTT pour le cours IFT785 - Devoir : Habitat Intelligent IoT
Module pour recevoir et traiter les donnees des capteurs IoT

Utilisation basique:
    from ift785_client import HabitatClient
    
    client = HabitatClient()
    while True:
        sensor_data = client.get_next_sensor_data()
        print(f"{sensor_data.location}: {sensor_data.value} {sensor_data.unit}")

@author: Hubert Ngankam
@version: 1.1 (avec mode simulation)
"""

import json
import queue
import threading
import random
import time
from typing import Optional, Dict, Any
from datetime import datetime
import paho.mqtt.client as mqtt


class SensorData:
    """
    Classe representant une mesure de capteur IoT
    
    Cette classe encapsule les donnees recues d'un capteur
    et fournit un acces facile aux differents champs.
    """
    
    def __init__(self, json_data: Dict[str, Any]):
        """
        Initialise un objet SensorData a partir d'un dictionnaire JSON
        
        Args:
            json_data: Dictionnaire contenant les donnees du capteur
        """
        self._sensor_id = json_data['sensorId']
        self._location = json_data['location']
        self._type = json_data['type']
        self._value = json_data['value']
        self._unit = json_data['unit']
        self._timestamp = json_data['timestamp']
    
    @property
    def sensor_id(self) -> str:
        """Identifiant unique du capteur (ex: TEMP_SALON_01)"""
        return self._sensor_id
    
    @property
    def location(self) -> str:
        """Emplacement du capteur (ex: salon, cuisine, chambre)"""
        return self._location
    
    @property
    def type(self) -> str:
        """Type de capteur (ex: temperature, lumiere, mouvement, consommation)"""
        return self._type
    
    @property
    def value(self) -> Any:
        """Valeur mesuree (le type varie selon le capteur)"""
        return self._value
    
    @property
    def unit(self) -> str:
        """Unite de mesure (ex: celsius, lux, boolean, watts)"""
        return self._unit
    
    @property
    def timestamp(self) -> str:
        """Horodatage ISO 8601 de la mesure"""
        return self._timestamp
    
    def __str__(self) -> str:
        """Representation textuelle du capteur"""
        return f"{self.sensor_id} ({self.location}/{self.type}): {self.value} {self.unit}"
    
    def __repr__(self) -> str:
        """Representation pour debogage"""
        return f"SensorData(id={self.sensor_id}, location={self.location}, " \
               f"type={self.type}, value={self.value})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'objet en dictionnaire
        
        Returns:
            Dictionnaire des donnees du capteur
        """
        return {
            'sensorId': self._sensor_id,
            'location': self._location,
            'type': self._type,
            'value': self._value,
            'unit': self._unit,
            'timestamp': self._timestamp
        }


class HabitatClient:
    """
    Client MQTT pour recevoir les donnees des capteurs IoT d'habitat intelligent
    
    Ce client se connecte automatiquement au broker et permet de recevoir
    les messages de tous les capteurs de l'habitat.
    
    Exemple:
        client = HabitatClient()
        
        # Recevoir des donnees
        while True:
            sensor_data = client.get_next_sensor_data()
            print(f"{sensor_data.location}: {sensor_data.value}")
        
        # Ou avec timeout
        sensor_data = client.get_next_sensor_data_timeout(5.0)
        if sensor_data:
            print(sensor_data)
    """
    
    # Configuration (hardcodee pour simplicite)
    _BROKER_HOST = "dinf-ift630.dinf.fsci.usherbrooke.ca"
    _BROKER_PORT = 1883
    _USERNAME = "ift630"
    _PASSWORD = "ift630"
    _TOPIC_ALL = "ift785/habitat/#"
    _CONNECTION_TIMEOUT = 5
    _SIMULATION_INTERVAL = 3
    
    def __init__(self, client_id: Optional[str] = None):
        """
        Initialise et connecte le client au broker MQTT
        
        Args:
            client_id: Identifiant client optionnel (genere automatiquement si None)
        
        Raises:
            RuntimeError: Si la connexion au broker echoue
        """
        # Generer un ID client unique si non fourni
        if client_id is None:
            import uuid
            client_id = f"ift785-student-{uuid.uuid4().hex[:8]}"
        
        # File de messages thread-safe
        self._message_queue = queue.Queue()
        
        # Etat de connexion
        self._connected = False
        self._simulation_mode = False
        self._connection_event = threading.Event()
        
        # Liste des locations pour simulation
        self._locations = ["salon", "cuisine", "chambre"]
        
        # Creer le client MQTT
        self._client = mqtt.Client(client_id=client_id)
        self._client.username_pw_set(self._USERNAME, self._PASSWORD)
        
        # Definir les callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        
        # Se connecter
        print(f"Tentative connexion MQTT ({self._BROKER_HOST})...")
        try:
            self._client.connect(self._BROKER_HOST, self._BROKER_PORT, keepalive=60)
            self._client.loop_start()
            
            # Attendre la connexion (timeout 5 secondes)
            if not self._connection_event.wait(timeout=self._CONNECTION_TIMEOUT):
                raise RuntimeError("Timeout de connexion au broker")
            
            print("CONNECTE au broker MQTT")
                
        except Exception as e:
            print(f"ECHEC connexion MQTT: {e}")
            print("PASSAGE en mode SIMULATION (donnees aleatoires)")
            self._simulation_mode = True
            self._start_simulation()
    
    def _start_simulation(self):
        """Demarre le thread de simulation"""
        sim_thread = threading.Thread(target=self._simulation_thread, daemon=True)
        sim_thread.start()
    
    def _simulation_thread(self):
        """Thread generant des donnees simulees"""
        while True:
            location = random.choice(self._locations)
            sensor_type = random.choice(['temperature', 'lumiere', 'mouvement', 'consommation'])
            
            if sensor_type == 'temperature':
                value = round(random.uniform(18, 25), 1)
                unit = 'celsius'
            elif sensor_type == 'lumiere':
                value = random.randint(0, 800)
                unit = 'lux'
            elif sensor_type == 'mouvement':
                value = random.choice([True, False])
                unit = 'boolean'
            else:
                value = round(random.uniform(100, 500), 1)
                unit = 'watts'
            
            sensor_id = f"{sensor_type.upper()}_{location.upper()}_01"
            timestamp = datetime.now().isoformat()
            
            data = {
                'sensorId': sensor_id,
                'location': location,
                'type': sensor_type,
                'value': value,
                'unit': unit,
                'timestamp': timestamp
            }
            
            self._message_queue.put(json.dumps(data))
            time.sleep(self._SIMULATION_INTERVAL)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback appele lors de la connexion au broker"""
        if rc == 0:
            self._connected = True
            self._connection_event.set()
            # S'abonner a tous les topics habitat
            client.subscribe(self._TOPIC_ALL, qos=0)
        else:
            self._connected = False
            print(f"Echec de connexion, code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback appele lors de la deconnexion"""
        self._connected = False
        if rc != 0:
            print(f"Deconnexion inattendue, reconnexion automatique...")
    
    def _on_message(self, client, userdata, message):
        """Callback appele a la reception d'un message"""
        payload = message.payload.decode('utf-8')
        self._message_queue.put(payload)
    
    def get_next_sensor_data(self) -> SensorData:
        """
        Recupere la prochaine donnee de capteur (bloquant)
        
        Cette methode attend qu'une donnee soit disponible.
        
        Returns:
            Objet SensorData contenant les donnees du capteur
        
        Raises:
            KeyboardInterrupt: Si Ctrl+C est presse
        """
        message = self._message_queue.get()
        json_data = json.loads(message)
        return SensorData(json_data)
    
    def get_next_sensor_data_timeout(self, timeout_sec: float) -> Optional[SensorData]:
        """
        Recupere la prochaine donnee avec timeout
        
        Args:
            timeout_sec: Timeout en secondes
        
        Returns:
            Objet SensorData ou None si timeout
        """
        try:
            message = self._message_queue.get(timeout=timeout_sec)
            json_data = json.loads(message)
            return SensorData(json_data)
        except queue.Empty:
            return None
    
    def get_next_message_raw(self) -> str:
        """
        Recupere le prochain message JSON brut (bloquant)
        
        Returns:
            Chaine JSON brute
        """
        return self._message_queue.get()
    
    def has_message(self) -> bool:
        """
        Verifie si des messages sont disponibles (non-bloquant)
        
        Returns:
            True si au moins un message est disponible
        """
        return not self._message_queue.empty()
    
    def get_queue_size(self) -> int:
        """
        Retourne le nombre de messages en attente
        
        Returns:
            Nombre de messages dans la file
        """
        return self._message_queue.qsize()
    
    def is_connected(self) -> bool:
        """
        Verifie si le client est connecte au broker
        
        Returns:
            True si connecte
        """
        if self._simulation_mode:
            return False
        return self._connected and self._client.is_connected()
    
    def is_simulation_mode(self) -> bool:
        """
        Verifie si le client est en mode simulation
        
        Returns:
            True si en mode simulation
        """
        return self._simulation_mode
    
    def subscribe_location(self, location: str):
        """
        Subscribe uniquement a une piece specifique
        
        Args:
            location: Nom de la piece (ex: "salon", "cuisine", "chambre")
        """
        if not self._simulation_mode:
            topic = f"ift785/habitat/{location}/#"
            self._client.subscribe(topic, qos=0)
    
    def subscribe_sensor_type(self, sensor_type: str):
        """
        Subscribe uniquement a un type de capteur
        
        Args:
            sensor_type: Type de capteur (ex: "temperature", "lumiere")
        """
        if not self._simulation_mode:
            topic = f"ift785/habitat/+/{sensor_type}"
            self._client.subscribe(topic, qos=0)
    
    def subscribe_all(self):
        """Subscribe a tous les capteurs (defaut)"""
        if not self._simulation_mode:
            self._client.subscribe(self._TOPIC_ALL, qos=0)
    
    def disconnect(self):
        """Deconnecte le client du broker"""
        if not self._simulation_mode:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False


# ============================================================================
# Exemple d'utilisation si execute directement
# ============================================================================

if __name__ == "__main__":
    print("=== IFT785 - Client Habitat IoT ===\n")
    
    # Creer le client
    client = HabitatClient()
    
    if client.is_simulation_mode():
        print("Mode: SIMULATION (donnees aleatoires)")
    else:
        print("Connecte au broker")
        print("Abonne aux topics ift785/habitat/#")
    
    print("\nEn attente de messages (Ctrl+C pour arreter)...\n")
    
    try:
        count = 0
        while True:
            # Recuperer les donnees du capteur
            sensor_data = client.get_next_sensor_data()
            
            count += 1
            print(f"Message #{count}: {sensor_data}")
            
    except KeyboardInterrupt:
        print("\n\nInterruption recue")
    finally:
        client.disconnect()
        print("Deconnecte")