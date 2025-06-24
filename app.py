#!/usr/bin/env python3
"""
NEUROSITY CROWN MONITOR - BACKEND OPTIMISÉ
"""

import os
import sys
import time
import threading
import multiprocessing as mp
from pathlib import Path
from datetime import datetime
from queue import Empty
from collections import deque
import statistics

# Flask et SocketIO
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit

# Configuration
from dotenv import load_dotenv

# DataManager local
from data_manager import DataManager

# ===============================================
# CONFIGURATION
# ===============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'neurosity_monitoring_secret'
app.static_folder = 'static'
app.template_folder = 'templates'

socketio = SocketIO(app, cors_allowed_origins="*")
manager = None


# ===============================================
# PROCESSUS NEUROSITY
# ===============================================

def neurosity_process(command_queue, data_queue, response_queue):
    """Processus séparé pour gérer le SDK Neurosity"""
    print("[NEUROSITY] Démarrage du processus...")
    
    try:
        from neurosity import NeurositySDK
    except ImportError:
        response_queue.put({'success': False, 'error': 'SDK Neurosity non installé'})
        return
    
    neurosity = None
    is_connected = False
    is_monitoring = False
    subscriptions = []
    battery_subscription = None
    device_status = {
        'online': False,
        'battery': 0,
        'charging': False,
        'signal': 'disconnected'
    }
    
    load_dotenv()
    
    def cleanup():
        """Nettoyage des ressources"""
        nonlocal neurosity, is_monitoring, subscriptions, is_connected, battery_subscription
        
        # Nettoyer les souscriptions
        for unsub in subscriptions + ([battery_subscription] if battery_subscription else []):
            if callable(unsub):
                try:
                    unsub()
                except:
                    pass
        
        subscriptions = []
        battery_subscription = None
        is_monitoring = False
        
        if neurosity and is_connected:
            try:
                neurosity.logout()
            except:
                pass
        
        neurosity = None
        is_connected = False
    
    def send_data(data_type, data):
        """Envoie des données via la queue"""
        try:
            message = {
                'type': data_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'device_status': device_status.copy()
            }
            data_queue.put(message, timeout=1)
        except:
            pass
    
    def detect_device():
        """Détecte si le casque est connecté et fonctionne"""
        print("[NEUROSITY] Détection du casque...")
        
        # Simple validation basée sur la réception de données
        data_received = {'calm': False, 'focus': False}
        test_subs = []
        
        def test_callback(metric):
            def callback(data):
                if data and 'probability' in data:
                    data_received[metric] = True
            
            return callback
        
        try:
            test_subs = [
                neurosity.calm(test_callback('calm')),
                neurosity.focus(test_callback('focus'))
            ]
            
            # Attendre les données pendant 5 secondes max
            for _ in range(50):
                if all(data_received.values()):
                    print("[NEUROSITY] Casque détecté et opérationnel")
                    return True
                time.sleep(0.1)
            
            print("[NEUROSITY] Pas de données reçues du casque")
            return False
        
        finally:
            for sub in test_subs:
                if callable(sub):
                    sub()
    
    # Callbacks pour les données
    def create_metric_callback(data_type):
        def callback(data):
            if data and 'probability' in data:
                send_data(data_type, {
                    'probability': data['probability'],
                    'percentage': data['probability'] * 100,
                    'timestamp': time.time() * 1000
                })
        
        return callback
    
    def brainwaves_callback(data):
        """Traite les données d'ondes cérébrales"""
        try:
            if not data or 'data' not in data:
                return
            
            bands_data = data['data']
            result = {}
            
            for wave in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                if wave in bands_data:
                    values = bands_data[wave]
                    if isinstance(values, list) and values:
                        # Calculer la moyenne des canaux
                        valid_values = [v for v in values if isinstance(v, (int, float)) and v >= 0]
                        result[wave] = round(sum(valid_values) / len(valid_values), 3) if valid_values else 0
                    else:
                        result[wave] = 0
                else:
                    result[wave] = 0
            
            result['timestamp'] = time.time() * 1000
            send_data('brainwaves', result)
        
        except Exception as e:
            print(f"[NEUROSITY] Erreur brainwaves: {e}")
    
    def signal_quality_callback(data):
        """Traite la qualité du signal des électrodes"""
        try:
            if isinstance(data, list) and len(data) == 8:
                electrodes = ['CP3', 'C3', 'F5', 'PO3', 'PO4', 'F6', 'C4', 'CP4']
                
                def status_to_quality(electrode_data):
                    status = electrode_data.get('status', 'bad')
                    if status == 'great':
                        return 0.95
                    elif status == 'good':
                        return 0.80
                    else:
                        return 0.30
                
                signal_dict = {
                    electrodes[i]: status_to_quality(data[i])
                    for i in range(min(len(data), len(electrodes)))
                }
                
                send_data('signal_quality', signal_dict)
        
        except Exception as e:
            print(f"[NEUROSITY] Erreur signal quality: {e}")
    
    def battery_callback(status):
        """Traite le statut de la batterie"""
        try:
            if isinstance(status, dict) and 'battery' in status:
                level = int(round(status.get('battery', 0)))
                charging = status.get('charging', False)
                
                device_status['battery'] = max(0, min(100, level))
                device_status['charging'] = charging
                
                send_data('battery', {
                    'level': device_status['battery'],
                    'charging': charging
                })
        
        except Exception as e:
            print(f"[NEUROSITY] Erreur battery: {e}")
    
    def brainwaves_raw_callback(data):
        """Traite les données EEG brutes"""
        if data:
            send_data('brainwaves_raw', data)
    
    # Boucle principale
    while True:
        try:
            command = command_queue.get(timeout=1)
            action = command.get('action')
            
            if action == 'connect':
                print("[NEUROSITY] Connexion...")
                try:
                    neurosity = NeurositySDK({
                        "device_id": os.getenv("NEUROSITY_DEVICE_ID")
                    })
                    
                    neurosity.login({
                        "email": os.getenv("NEUROSITY_EMAIL"),
                        "password": os.getenv("NEUROSITY_PASSWORD")
                    })
                    
                    if detect_device():
                        is_connected = True
                        device_status['online'] = True
                        device_status['signal'] = 'excellent'
                        
                        # Récupérer le statut initial
                        try:
                            initial_status = neurosity.status()
                            if isinstance(initial_status, dict):
                                device_status['battery'] = int(round(initial_status.get('battery', 0)))
                                device_status['charging'] = initial_status.get('charging', False)
                        except:
                            pass
                        
                        # S'abonner au statut batterie
                        battery_subscription = neurosity.status(battery_callback)
                        
                        response_queue.put({
                            'success': True,
                            'connected': True,
                            'device_status': device_status,
                            'message': 'Casque Neurosity connecté !'
                        })
                    else:
                        cleanup()
                        response_queue.put({
                            'success': False,
                            'error': 'Casque non détecté. Vérifiez qu\'il est allumé et porté.'
                        })
                except Exception as e:
                    cleanup()
                    response_queue.put({'success': False, 'error': str(e)})
            
            elif action == 'start_monitoring':
                if not is_connected:
                    response_queue.put({'success': False, 'error': 'Non connecté'})
                    continue
                
                if not is_monitoring:
                    print("[NEUROSITY] Démarrage du monitoring...")
                    
                    # S'abonner à toutes les métriques
                    subscriptions = [
                        neurosity.calm(create_metric_callback('calm')),
                        neurosity.focus(create_metric_callback('focus')),
                        neurosity.brainwaves_power_by_band(brainwaves_callback),
                        neurosity.signal_quality(signal_quality_callback),
                        neurosity.brainwaves_raw(brainwaves_raw_callback)
                    ]
                    
                    is_monitoring = True
                    print("[NEUROSITY] 🎯 Monitoring actif")
                
                response_queue.put({'success': True, 'monitoring': True})
            
            elif action == 'stop_monitoring':
                if subscriptions:
                    for sub in subscriptions:
                        if callable(sub):
                            sub()
                    subscriptions = []
                is_monitoring = False
                response_queue.put({'success': True, 'monitoring': False})
            
            elif action == 'disconnect':
                cleanup()
                response_queue.put({'success': True, 'connected': False})
            
            elif action == 'quit':
                break
        
        except Empty:
            continue
        except Exception as e:
            print(f"[NEUROSITY] Erreur: {e}")
    
    cleanup()
    print("[NEUROSITY] Processus terminé")


# ===============================================
# GESTIONNAIRE NEUROSITY
# ===============================================

class NeurosityManager:
    """Gestionnaire principal pour l'interface avec Neurosity"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.is_recording = False
        self.is_connected = False
        self.is_monitoring = False
        self.device_status = {
            'online': False,
            'battery': 0,
            'charging': False,
            'signal': 'disconnected'
        }
        
        # Processus et queues
        self.command_queue = None
        self.data_queue = None
        self.response_queue = None
        self.neurosity_process = None
        
        print("Manager Neurosity initialisé")
    
    def start_process(self):
        """Démarre le processus Neurosity"""
        try:
            self.command_queue = mp.Queue()
            self.data_queue = mp.Queue()
            self.response_queue = mp.Queue()
            
            self.neurosity_process = mp.Process(
                target=neurosity_process,
                args=(self.command_queue, self.data_queue, self.response_queue)
            )
            self.neurosity_process.start()
            return True
        except Exception as e:
            print(f"Erreur démarrage processus: {e}")
            return False
    
    def stop_process(self):
        """Arrête le processus Neurosity"""
        try:
            if self.command_queue:
                self.command_queue.put({'action': 'quit'})
            
            if self.neurosity_process and self.neurosity_process.is_alive():
                self.neurosity_process.join(timeout=5)
                if self.neurosity_process.is_alive():
                    self.neurosity_process.terminate()
        except:
            pass
    
    def send_command(self, action, timeout=30):
        """Envoie une commande au processus"""
        try:
            self.command_queue.put({'action': action})
            return self.response_queue.get(timeout=timeout)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def process_data(self):
        """Traite les données reçues du processus"""
        try:
            processed = 0
            while processed < 10:  # Limiter le traitement par cycle
                try:
                    message = self.data_queue.get_nowait()
                    processed += 1
                    
                    data_type = message['type']
                    data = message['data']
                    
                    # Préparer les données pour l'émission
                    emit_data = {
                        'timestamp': message['timestamp'],
                        'type': data_type,
                        'device_status': message.get('device_status', {})
                    }
                    
                    if data_type in ['calm', 'focus']:
                        emit_data[data_type] = data.get('percentage', 0)
                    elif data_type == 'brainwaves':
                        emit_data.update(data)
                    elif data_type == 'signal_quality':
                        emit_data.update(data)
                    elif data_type == 'battery':
                        emit_data.update(data)
                        self.device_status.update(data)
                    elif data_type == 'brainwaves_raw':
                        emit_data['raw_data'] = data.get('data', [])
                        emit_data['info'] = data.get('info', {})
                    
                    # Émettre via WebSocket
                    socketio.emit(f'{data_type}_data', emit_data)
                    
                    # Enregistrer si nécessaire
                    if self.is_recording and data_type in ['calm', 'focus', 'brainwaves']:
                        self.data_manager.add_data_point(data_type, data)
                
                except Empty:
                    break
        except Exception as e:
            print(f"Erreur traitement données: {e}")
    
    def start_recording(self, filename=None):
        """Démarre l'enregistrement"""
        try:
            if not self.is_connected:
                return False
            
            self.data_manager.start_session(filename)
            self.is_recording = True
            return True
        except:
            return False
    
    def stop_recording(self):
        """Arrête l'enregistrement"""
        try:
            if self.is_recording:
                session_file = self.data_manager.stop_session()
                self.is_recording = False
                return session_file
        except:
            pass
        return None


# ===============================================
# ROUTES FLASK
# ===============================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/connect', methods=['POST'])
def connect_device():
    try:
        response = manager.send_command('connect', timeout=35)
        if response['success']:
            manager.is_connected = True
            manager.device_status = response.get('device_status', {})
        return jsonify(response)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/disconnect', methods=['POST'])
def disconnect_device():
    try:
        response = manager.send_command('disconnect')
        if response['success']:
            manager.is_connected = False
            manager.is_monitoring = False
            manager.device_status = {
                'online': False,
                'battery': 0,
                'charging': False,
                'signal': 'disconnected'
            }
        return jsonify(response)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/start_recording', methods=['POST'])
def start_recording():
    try:
        if not manager.is_connected:
            return jsonify({'success': False, 'error': 'Non connecté'})
        
        filename = request.json.get('filename') if request.is_json else None
        success = manager.start_recording(filename)
        
        return jsonify({
            'success': success,
            'recording': manager.is_recording
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    try:
        session_file = manager.stop_recording()
        return jsonify({
            'success': True,
            'recording': False,
            'session_file': session_file
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/sessions')
def get_sessions():
    try:
        sessions = manager.data_manager.get_session_list()
        return jsonify({'sessions': sessions})
    except:
        return jsonify({'sessions': []})


@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(manager.data_manager.data_directory, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        return jsonify({'error': 'Fichier non trouvé'}), 404
    except:
        return jsonify({'error': 'Erreur'}), 500


@app.route('/status')
def get_status():
    return jsonify({
        'connected': manager.is_connected,
        'recording': manager.is_recording,
        'monitoring': manager.is_monitoring,
        'device_status': manager.device_status,
        'sessions_count': len(manager.data_manager.get_session_list())
    })


# ===============================================
# HANDLERS SOCKETIO
# ===============================================

@socketio.on('connect')
def handle_connect():
    print('🔌 Client WebSocket connecté')
    emit('status', {
        'connected': manager.is_connected,
        'recording': manager.is_recording,
        'monitoring': manager.is_monitoring,
        'device_status': manager.device_status
    })


@socketio.on('disconnect')
def handle_disconnect():
    print('🔌 Client WebSocket déconnecté')


@socketio.on('start_monitoring')
def handle_start_monitoring(data=None):
    try:
        if not manager.is_connected:
            emit('error', {'message': 'Non connecté'})
            return
        
        response = manager.send_command('start_monitoring')
        if response['success']:
            manager.is_monitoring = True
            emit('monitoring_started', {'success': True})
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('stop_monitoring')
def handle_stop_monitoring(data=None):
    try:
        response = manager.send_command('stop_monitoring')
        manager.is_monitoring = False
        emit('monitoring_stopped', {'success': True})
    except Exception as e:
        emit('error', {'message': str(e)})


# ===============================================
# THREAD DE TRAITEMENT
# ===============================================

def data_processor():
    """Thread qui traite les données en continu"""
    print("Démarrage du processeur de données...")
    
    while True:
        try:
            if manager:
                manager.process_data()
            time.sleep(0.05)
        except Exception as e:
            print(f"Erreur processeur: {e}")
            time.sleep(1)


# ===============================================
# FONCTIONS UTILITAIRES
# ===============================================

def check_environment():
    """Vérifie la configuration"""
    env_file = Path('.env')
    if not env_file.exists():
        print("Fichier .env manquant")
        return False
    
    load_dotenv()
    
    required = ['NEUROSITY_EMAIL', 'NEUROSITY_PASSWORD', 'NEUROSITY_DEVICE_ID']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"Variables manquantes: {', '.join(missing)}")
        return False
    
    Path('data').mkdir(exist_ok=True)
    print("Environnement vérifié")
    return True


# ===============================================
# MAIN
# ===============================================

def main():
    global manager
    
    print("\n" + "=" * 60)
    print("NEUROSITY CROWN MONITOR")
    print("=" * 60)
    
    if not check_environment():
        sys.exit(1)
    
    # Initialiser le manager
    manager = NeurosityManager()
    
    if not manager.start_process():
        print("Impossible de démarrer le processus Neurosity")
        sys.exit(1)
    
    # Démarrer le thread de traitement
    data_thread = threading.Thread(target=data_processor, daemon=True)
    data_thread.start()
    
    # Configuration du serveur
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print(f"\nServeur prêt sur http://localhost:{port}")
    print("\nInstructions:")
    print("1. Allumez votre casque Neurosity Crown")
    print("2. Portez-le correctement")
    print("3. Cliquez 'Connecter' dans l'interface")
    print("4. Observez vos ondes cérébrales en temps réel !")
    print("=" * 60 + "\n")
    
    try:
        socketio.run(
            app,
            debug=False,
            host=host,
            port=port,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\nArrêt...")
    finally:
        manager.stop_process()
        print("Application fermée")


if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    main()