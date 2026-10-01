#!/usr/bin/env python3
"""
NEUROSITY CROWN MONITOR - VERSION AVEC WORKER SÃ‰PARÃ‰
RÃ©sout le problÃ¨me multiprocessing de PyInstaller en isolant le worker
"""

import os
import sys
import multiprocessing as mp

# Configuration multiprocessing AVANT tout
if __name__ == "__main__":
    mp.freeze_support()
    if sys.platform == "win32":
        mp.set_start_method('spawn', force=True)

import time
import threading
from pathlib import Path
from datetime import datetime
from queue import Empty
import webbrowser
import logging
import tempfile
import atexit
import socket

# Ajouter l'import
from csv_viewer_routes import register_csv_viewer_routes

# Traductions serveur (FR par defaut, EN disponible)
import i18n as i18n_module
from i18n import t as _t, normalize_lang, SUPPORTED_LANGS, LANG_COOKIE, DEFAULT_LANG

# Flask et SocketIO
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit

# Configuration
from dotenv import load_dotenv

# DataManager local
from data_manager import DataManager

# IMPORTANT: Import du worker sÃ©parÃ© pour PyInstaller
from neurosity_worker import neurosity_process

# ===============================================
# CONFIGURATION
# ===============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ACTUAL_PORT = None

# Gestion chemins PyInstaller
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
    template_folder = os.path.join(application_path, 'templates')
    static_folder = os.path.join(application_path, 'static')
    # IMPORTANT: Le dossier data doit être dans le répertoire de l'exe, pas dans _MEIPASS
    data_directory = os.path.join(os.path.dirname(sys.executable), 'data')
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
    template_folder = 'templates'
    static_folder = 'static'
    data_directory = 'data'


# ===============================================
# SYSTÃˆME DE VERROUILLAGE
# ===============================================

class BrowserLock:
    def __init__(self):
        self.lock_file = Path(tempfile.gettempdir()) / "neurosity_browser.lock"
        self.lock_acquired = False
        self.pid = os.getpid()
    
    def acquire(self):
        try:
            if self.lock_file.exists():
                try:
                    with open(self.lock_file, 'r') as f:
                        stored_pid = int(f.read().strip())
                    try:
                        os.kill(stored_pid, 0)
                        logger.info(f"Instance dÃ©jÃ  en cours (PID: {stored_pid})")
                        return False
                    except OSError:
                        logger.info("Ancien verrou nettoyÃ©")
                        self.lock_file.unlink()
                except:
                    self.lock_file.unlink()
            
            with open(self.lock_file, 'w') as f:
                f.write(str(self.pid))
            
            self.lock_acquired = True
            atexit.register(self.release)
            return True
        except Exception as e:
            logger.error(f"Erreur verrou: {e}")
            return False
    
    def release(self):
        try:
            if self.lock_acquired and self.lock_file.exists():
                with open(self.lock_file, 'r') as f:
                    stored_pid = int(f.read().strip())
                if stored_pid == self.pid:
                    self.lock_file.unlink()
                    self.lock_acquired = False
        except:
            pass


browser_lock = BrowserLock()
_app_initialized = False

# App Flask
templates_path = Path(template_folder)
templates_path.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
app.config['SECRET_KEY'] = 'neurosity_monitoring_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
manager = None
config_manager = None

# Exposer `lang` et `t` aux templates Jinja
i18n_module.register_i18n(app)

# Enregistrer les routes de visualisation CSV
register_csv_viewer_routes(app, data_directory=data_directory)


# ===============================================
# GESTIONNAIRE DE CONFIGURATION
# ===============================================

class ConfigManager:
    def __init__(self, config_path: str = "config/user_config.enc"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            from cryptography.fernet import Fernet
            self.encryption_key = self._get_or_create_encryption_key()
            self.cipher = Fernet(self.encryption_key)
            self.encryption_available = True
        except ImportError:
            logger.warning("Cryptography non disponible")
            self.encryption_available = False
            self.cipher = None
        
        self.default_config = {
            "device_id": "",
            "email": "",
            "password": "",
            "auto_connect": False,
            "remember_credentials": True,
            "language": DEFAULT_LANG,
            "last_updated": None
        }
    
    def _get_or_create_encryption_key(self):
        from cryptography.fernet import Fernet
        key_file = Path("config/.key")
        key_file.parent.mkdir(parents=True, exist_ok=True)
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            try:
                os.chmod(key_file, 0o600)
            except:
                pass
            return key
    
    def save_config(self, config: dict) -> bool:
        if not self.encryption_available:
            return False
        try:
            import json
            config['last_updated'] = datetime.now().isoformat()
            json_data = json.dumps(config, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            with open(self.config_path, 'wb') as f:
                f.write(encrypted_data)
            try:
                os.chmod(self.config_path, 0o600)
            except:
                pass
            logger.info(f"Configuration sauvegardÃ©e")
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
            return False
    
    def load_config(self) -> dict:
        if not self.encryption_available:
            return self.default_config.copy()
        try:
            import json
            if not self.config_path.exists():
                return self.default_config.copy()
            with open(self.config_path, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher.decrypt(encrypted_data)
            config = json.loads(decrypted_data.decode())
            final_config = self.default_config.copy()
            final_config.update(config)
            logger.info("Configuration chargÃ©e")
            return final_config
        except Exception as e:
            logger.error(f"Erreur chargement: {e}")
            return self.default_config.copy()
    
    def get_neurosity_credentials(self) -> dict:
        config = self.load_config()
        return {
            'device_id': config.get('device_id', ''),
            'email': config.get('email', ''),
            'password': config.get('password', '')
        }
    
    def update_credentials(self, device_id: str, email: str, password: str,
                           auto_connect: bool = False, remember: bool = True) -> bool:
        config = self.load_config()
        config['device_id'] = device_id
        config['email'] = email
        if remember:
            config['password'] = password
        else:
            config['password'] = ""
        config['auto_connect'] = auto_connect
        config['remember_credentials'] = remember
        return self.save_config(config)
    
    def clear_credentials(self) -> bool:
        config = self.default_config.copy()
        return self.save_config(config)
    
    def get_language(self) -> str:
        config = self.load_config()
        return normalize_lang(config.get('language'))

    def set_language(self, language: str) -> bool:
        config = self.load_config()
        config['language'] = normalize_lang(language)
        return self.save_config(config)

    def get_current_config(self) -> dict:
        config = self.load_config()
        display_config = config.copy()
        if display_config.get('password'):
            display_config['password'] = 'â€¢' * 8
        return display_config
    
    def test_connection(self, device_id: str, email: str, password: str) -> dict:
        try:
            from neurosity import NeurositySDK
            neurosity = NeurositySDK({"device_id": device_id})
            neurosity.login({"email": email, "password": password})
            neurosity.logout()
            return {'success': True, 'message': _t('test_success'), 'code': 'test_success'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def migrate_from_env(self) -> bool:
        if not self.encryption_available:
            return False
        try:
            load_dotenv()
            device_id = os.getenv('NEUROSITY_DEVICE_ID', '')
            email = os.getenv('NEUROSITY_EMAIL', '')
            password = os.getenv('NEUROSITY_PASSWORD', '')
            if device_id and email and password:
                logger.info("Migration depuis .env...")
                return self.update_credentials(device_id, email, password, False, True)
            return False
        except Exception as e:
            logger.error(f"Erreur migration: {e}")
            return False


# ===============================================
# GESTIONNAIRE NEUROSITY
# ===============================================

class NeurosityManager:
    def __init__(self):
        self.data_manager = DataManager(data_directory=data_directory)
        self.is_recording = False
        self.is_connected = False
        self.is_monitoring = False
        self.device_status = {
            'online': False,
            'battery': 0,
            'charging': False,
            'signal': 'disconnected'
        }
        
        self.command_queue = None
        self.data_queue = None
        self.response_queue = None
        self.neurosity_process = None
        self.data_thread = None
        self.running = False
        
        logger.info("Manager initialisÃ©")
    
    def start_process(self):
        try:
            ctx = mp.get_context('spawn')
            self.command_queue = ctx.Queue()
            self.data_queue = ctx.Queue()
            self.response_queue = ctx.Queue()
            
            # IMPORTANT: Utilise neurosity_process du module neurosity_worker
            self.neurosity_process = ctx.Process(
                target=neurosity_process,
                args=(self.command_queue, self.data_queue, self.response_queue),
                name='NeurosityWorker'
            )
            self.neurosity_process.daemon = True
            self.neurosity_process.start()
            
            time.sleep(1)
            
            self.running = True
            self.data_thread = threading.Thread(target=self._data_processor, daemon=True)
            self.data_thread.start()
            
            logger.info("Processus dÃ©marrÃ©")
            return True
        except Exception as e:
            logger.error(f"Erreur dÃ©marrage: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_process(self):
        self.running = False
        if self.command_queue:
            try:
                self.command_queue.put({'action': 'quit'})
            except:
                pass
        if self.neurosity_process and self.neurosity_process.is_alive():
            self.neurosity_process.join(timeout=5)
            if self.neurosity_process.is_alive():
                self.neurosity_process.terminate()
                self.neurosity_process.join(timeout=2)
        if self.data_thread and self.data_thread.is_alive():
            self.data_thread.join(timeout=2)
        logger.info("Module arrÃªtÃ©")
    
    def _data_processor(self):
        logger.info("Processeur de donnÃ©es dÃ©marrÃ©")
        while self.running:
            try:
                for _ in range(10):
                    try:
                        message = self.data_queue.get_nowait()
                        self._handle_data_message(message)
                    except Empty:
                        break
                time.sleep(0.05)
            except Exception as e:
                logger.error(f"Erreur processeur: {e}")
                time.sleep(1)
    
    def _handle_data_message(self, message):
        try:
            data_type = message['type']
            data = message['data']
            timestamp = message['timestamp']
            device_status = message.get('device_status', {})
            
            self.device_status.update(device_status)
            
            emit_data = {'timestamp': timestamp, 'device_status': self.device_status}
            
            if data_type == 'calm':
                emit_data['calm'] = data.get('percentage', 0)
                socketio.emit('calm_data', emit_data)
                if self.is_recording:
                    self.data_manager.add_data_point('calm', data)
            
            elif data_type == 'focus':
                emit_data['focus'] = data.get('percentage', 0)
                socketio.emit('focus_data', emit_data)
                if self.is_recording:
                    self.data_manager.add_data_point('focus', data)
            
            elif data_type == 'brainwaves':
                # Les donnÃ©es contiennent dÃ©jÃ  les 8 valeurs par bande
                emit_data.update(data)  # Inclut delta, theta, alpha, beta, gamma avec leurs 8 valeurs
                socketio.emit('brainwaves_data', emit_data)
                
                # Log pour debug
                logger.debug(f"Ã‰mission brainwaves_data: {list(data.keys())}")
                
                if self.is_recording:
                    self.data_manager.add_data_point('brainwaves', data)
            
            elif data_type == 'signal_quality':
                emit_data.update(data)
                socketio.emit('signal_quality_data', emit_data)
                if self.is_recording:
                    self.data_manager.add_data_point('signal_quality', data)
            
            elif data_type == 'battery':
                emit_data.update(data)
                socketio.emit('battery_data', emit_data)
            
            elif data_type == 'brainwaves_raw':
                emit_data['raw_data'] = data.get('data', [])
                emit_data['info'] = data.get('info', {})
                socketio.emit('brainwaves_raw_data', emit_data)
                if self.is_recording:
                    self.data_manager.add_data_point('brainwaves_raw', data)
        
        except Exception as e:
            logger.error(f"Erreur traitement: {e}")
    
    def send_command(self, action, credentials=None, timeout=30):
        try:
            if not self.command_queue:
                return {'success': False, 'error': _t('module_not_ready'), 'code': 'module_not_ready'}
            
            while True:
                try:
                    self.response_queue.get_nowait()
                except Empty:
                    break
            
            command = {'action': action}
            if credentials:
                command['credentials'] = credentials
            
            self.command_queue.put(command)
            return self.response_queue.get(timeout=timeout)
        except Exception as e:
            logger.error(f"Erreur commande: {e}")
            return {'success': False, 'error': str(e)}
    
    def start_recording(self, filename=None):
        try:
            if not self.is_connected:
                return {'success': False, 'error': _t('not_connected'), 'code': 'not_connected', 'recording': False}
            session_file = self.data_manager.start_session(filename)
            self.is_recording = True
            logger.info(f"Enregistrement: {session_file}")
            return {'success': True, 'recording': True, 'session_file': session_file}
        except Exception as e:
            logger.error(f"Erreur enregistrement: {e}")
            return {'success': False, 'error': str(e), 'recording': False}
    
    def stop_recording(self):
        try:
            session_file = None
            if self.is_recording:
                session_file = self.data_manager.stop_session()
                self.is_recording = False
                logger.info(f"Enregistrement arrÃªtÃ©")
            return {'success': True, 'recording': False, 'session_file': session_file}
        except Exception as e:
            logger.error(f"Erreur arrÃªt: {e}")
            return {'success': False, 'error': str(e), 'recording': self.is_recording}
    
    def get_sessions_list(self):
        try:
            return self.data_manager.get_session_list()
        except Exception as e:
            logger.error(f"Erreur sessions: {e}")
            return []
    
    def get_status(self):
        return {
            'connected': self.is_connected,
            'monitoring': self.is_monitoring,
            'recording': self.is_recording,
            'device_status': self.device_status,
            'sessions_count': len(self.get_sessions_list())
        }


# ===============================================
# ROUTES FLASK (simplifiÃ©es)
# ===============================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/api/language', methods=['GET', 'POST'])
def language_preference():
    """Lit ou enregistre la langue de l'interface (FR par defaut, EN disponible)."""
    try:
        if request.method == 'GET':
            current = request.cookies.get(LANG_COOKIE)
            if not current and config_manager:
                current = config_manager.get_language()
            return jsonify({'success': True, 'language': normalize_lang(current)})

        data = request.json or {}
        requested = str(data.get('language', '')).strip().lower()[:2]

        if requested not in SUPPORTED_LANGS:
            return jsonify({
                'success': False,
                'error': _t('unsupported_language'),
                'code': 'unsupported_language',
                'supported': list(SUPPORTED_LANGS)
            }), 400

        # Persiste dans la configuration chiffree (best effort)
        if config_manager:
            try:
                config_manager.set_language(requested)
            except Exception as e:
                logger.warning(f"Langue non persistee dans la configuration: {e}")

        response = jsonify({
            'success': True,
            'language': requested,
            'message': _t('language_saved', lang=requested),
            'code': 'language_saved'
        })
        response.set_cookie(
            LANG_COOKIE, requested,
            max_age=31536000, path='/', samesite='Lax'
        )
        logger.info(f"Langue de l'interface: {requested}")
        return response

    except Exception as e:
        logger.error(f"Erreur preference de langue: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.after_request
def ensure_language_cookie(response):
    """Aligne le cookie de langue sur la preference enregistree au 1er affichage."""
    try:
        if request.cookies.get(LANG_COOKIE) is None and config_manager:
            if response.mimetype == 'text/html':
                response.set_cookie(
                    LANG_COOKIE, config_manager.get_language(),
                    max_age=31536000, path='/', samesite='Lax'
                )
    except Exception:
        pass
    return response


@app.route('/api/settings/current')
def get_current_settings():
    try:
        config = config_manager.get_current_config()
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/settings/save', methods=['POST'])
def save_settings():
    try:
        data = request.json
        success = config_manager.update_credentials(
            device_id=data.get('device_id', ''),
            email=data.get('email', ''),
            password=data.get('password', ''),
            auto_connect=data.get('auto_connect', False),
            remember=data.get('remember_credentials', True)
        )
        if success:
            return jsonify({'success': True, 'message': _t('config_saved'), 'code': 'config_saved'})
        else:
            return jsonify({'success': False, 'error': _t('save_failed'), 'code': 'save_failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/settings/test', methods=['POST'])
def test_settings():
    try:
        data = request.json
        result = config_manager.test_connection(
            device_id=data.get('device_id', ''),
            email=data.get('email', ''),
            password=data.get('password', '')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/settings/clear', methods=['POST'])
def clear_settings():
    try:
        success = config_manager.clear_credentials()
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/connect', methods=['POST'])
def connect_device():
    try:
        credentials = config_manager.get_neurosity_credentials()
        if not all([credentials.get('device_id'), credentials.get('email'), credentials.get('password')]):
            load_dotenv()
            credentials = {
                'device_id': os.getenv("NEUROSITY_DEVICE_ID", ""),
                'email': os.getenv("NEUROSITY_EMAIL", ""),
                'password': os.getenv("NEUROSITY_PASSWORD", "")
            }
        
        if not all([credentials.get('device_id'), credentials.get('email'), credentials.get('password')]):
            return jsonify({
                'success': False,
                'error': _t('missing_config'),
                'code': 'missing_config'
            })
        
        response = manager.send_command('connect', credentials=credentials, timeout=60)
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
        filename = request.json.get('filename') if request.is_json else None
        result = manager.start_recording(filename)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    try:
        result = manager.stop_recording()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/sessions')
def get_sessions():
    try:
        sessions = manager.get_sessions_list()
        return jsonify({'sessions': sessions})
    except:
        return jsonify({'sessions': []})


@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = manager.data_manager.data_directory / filename
        if file_path.exists():
            return send_file(file_path, as_attachment=True)
        return jsonify({'error': _t('file_not_found'), 'code': 'file_not_found'}), 404
    except:
        return jsonify({'error': _t('error'), 'code': 'error'}), 500


@app.route('/analyze/<filename>')
def analyze_session(filename):
    try:
        analysis = manager.data_manager.analyze_session(filename)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/status')
def get_status():
    return jsonify(manager.get_status())


@app.route('/storage_info')
def get_storage_info():
    try:
        info = manager.data_manager.get_storage_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# SOCKETIO

@socketio.on('connect')
def handle_connect():
    logger.info('Client WebSocket connectÃ©')
    emit('status', manager.get_status())


@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client WebSocket dÃ©connectÃ©')


@socketio.on('start_monitoring')
def handle_start_monitoring(data=None):
    try:
        if not manager.is_connected:
            emit('error', {'message': _t('not_connected'), 'code': 'not_connected'})
            return
        response = manager.send_command('start_monitoring')
        if response['success']:
            manager.is_monitoring = True
            emit('monitoring_started', {'success': True})
            logger.info("Monitoring dÃ©marrÃ©")
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('stop_monitoring')
def handle_stop_monitoring(data=None):
    try:
        response = manager.send_command('stop_monitoring')
        if response['success']:
            manager.is_monitoring = False
            emit('monitoring_stopped', {'success': True})
            logger.info("Monitoring arrÃªtÃ©")
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('get_status')
def handle_get_status():
    emit('status_update', manager.get_status())


@socketio.on('get_sessions')
def handle_get_sessions():
    sessions = manager.get_sessions_list()
    emit('sessions_list', {'sessions': sessions})


# ===============================================
# UTILITAIRES
# ===============================================

def is_port_in_use(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except:
        return False


def find_free_port(start_port=5000, max_attempts=10):
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None


def check_environment():
    if config_manager and config_manager.encryption_available:
        credentials = config_manager.get_neurosity_credentials()
        if all([credentials.get('device_id'), credentials.get('email'), credentials.get('password')]):
            logger.info("Configuration trouvÃ©e")
            Path('data').mkdir(exist_ok=True)
            return True
    
    env_file = Path('.env')
    if not env_file.exists():
        logger.warning("Pas de configuration")
        logger.info("Allez sur /settings")
        Path('data').mkdir(exist_ok=True)
        return True
    
    load_dotenv()
    required_vars = ['NEUROSITY_EMAIL', 'NEUROSITY_PASSWORD', 'NEUROSITY_DEVICE_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Variables manquantes: {', '.join(missing_vars)}")
        logger.info("Allez sur /settings")
    
    Path('data').mkdir(exist_ok=True)
    logger.info("Environnement vÃ©rifiÃ©")
    return True


def cleanup():
    logger.info("Nettoyage...")
    if manager:
        if manager.is_recording:
            manager.stop_recording()
        if manager.is_connected:
            manager.send_command('disconnect')
        manager.stop_process()
    browser_lock.release()


def safe_open_browser(port):
    if browser_lock.acquire():
        time.sleep(3)
        url = f'http://localhost:{port}'
        max_retries = 10
        for i in range(max_retries):
            try:
                import requests
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    logger.info(f"Ouverture: {url}")
                    webbrowser.open(url)
                    return
            except:
                if i < max_retries - 1:
                    time.sleep(0.5)
        logger.info(f"Ouverture: {url}")
        webbrowser.open(url)
    else:
        logger.info("Navigateur dÃ©jÃ  ouvert")


def run_server():
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    if is_port_in_use(port):
        logger.warning(f"Port {port} utilisÃ©")
        free_port = find_free_port(port)
        if free_port:
            logger.info(f"Port {free_port}")
            port = free_port
        else:
            logger.error("Aucun port libre")
            print(f"\nERREUR: Port {port} utilisÃ©!")
            input("\nAppuyez sur EntrÃ©e...")
            sys.exit(1)
    
    global ACTUAL_PORT
    ACTUAL_PORT = port
    
    try:
        socketio.run(app, debug=False, host=host, port=port, use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)
    except OSError as e:
        if "10048" in str(e) or "address already in use" in str(e).lower():
            logger.error(f"Port {port} bloquÃ©")
            print(f"\nPort {port} bloquÃ©")
            input("\nAppuyez sur EntrÃ©e...")
        else:
            logger.error(f"Erreur: {e}")
            raise


# ===============================================
# MAIN
# ===============================================

def main():
    global manager, config_manager, _app_initialized, ACTUAL_PORT
    
    if _app_initialized:
        logger.warning("DÃ©jÃ  initialisÃ©")
        return
    
    _app_initialized = True
    
    print("\n" + "=" * 60)
    print("NEUROSITY CROWN MONITOR - VERSION WORKER SÃ‰PARÃ‰")
    print("=" * 60)
    print(f"Processus: {mp.current_process().name}, PID: {os.getpid()}")
    
    config_manager = ConfigManager()
    config_manager.migrate_from_env()
    
    if not check_environment():
        sys.exit(1)
    
    manager = NeurosityManager()
    
    if not manager.start_process():
        logger.error("Erreur dÃ©marrage processus")
        sys.exit(1)
    
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    if is_port_in_use(port):
        free_port = find_free_port(port)
        if free_port:
            port = free_port
    
    ACTUAL_PORT = port
    
    console_lang = config_manager.get_language() if config_manager else DEFAULT_LANG

    print(f"\n{_t('console.ready', console_lang)}: http://localhost:{port}")
    print(f"{_t('console.settings', console_lang)}: http://localhost:{port}/settings")
    print(f"\n{_t('console.instructions', console_lang)}:")
    for step in range(1, 6):
        print(f"{step}. {_t(f'console.step{step}', console_lang)}")
    print("=" * 60 + "\n")
    
    browser_thread = threading.Thread(target=safe_open_browser, args=(ACTUAL_PORT,), daemon=True)
    browser_thread.start()
    
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n\nArrÃªt...")
    finally:
        cleanup()
        print("Application fermÃ©e")


# ===============================================
# POINT D'ENTRÃ‰E
# ===============================================

if __name__ == "__main__":
    current_process = mp.current_process()
    print(f"[DEBUG] Processus: {current_process.name}, PID: {os.getpid()}")
    
    if current_process.name == 'MainProcess':
        main()
    else:
        print(f"[DEBUG] Processus enfant: {current_process.name}")