"""
Configuration centralisée pour l'application Neurosity Monitor - Version Corrigée
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Répertoire racine du projet
BASE_DIR = Path(__file__).parent.parent

# Charger les variables d'environnement
load_dotenv(BASE_DIR / '.env')


class Config:
    """Configuration de base"""
    
    # Configuration Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'neurosity_monitoring_secret_key_change_in_production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configuration serveur
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Configuration Neurosity
    NEUROSITY_EMAIL = os.getenv('NEUROSITY_EMAIL')
    NEUROSITY_PASSWORD = os.getenv('NEUROSITY_PASSWORD')
    NEUROSITY_DEVICE_ID = os.getenv('NEUROSITY_DEVICE_ID')
    
    # Configuration des données
    DATA_DIRECTORY = BASE_DIR / 'data'
    MAX_SESSION_DURATION = int(os.getenv('MAX_SESSION_DURATION', 7200))  # 2 heures par défaut
    CSV_DELIMITER = os.getenv('CSV_DELIMITER', ';')
    
    # CORRECTION: Configuration de nettoyage automatique
    AUTO_CLEANUP_ENABLED = os.getenv('AUTO_CLEANUP_ENABLED', 'True').lower() == 'true'
    DAYS_TO_KEEP_SESSIONS = int(os.getenv('DAYS_TO_KEEP_SESSIONS', 30))
    MAX_STORAGE_MB = int(os.getenv('MAX_STORAGE_MB', 1000))  # 1GB par défaut
    
    # Configuration WebSocket
    WEBSOCKET_TIMEOUT = int(os.getenv('WEBSOCKET_TIMEOUT', 60))
    MAX_RECONNECT_ATTEMPTS = int(os.getenv('MAX_RECONNECT_ATTEMPTS', 5))
    WEBSOCKET_PING_INTERVAL = int(os.getenv('WEBSOCKET_PING_INTERVAL', 25))
    WEBSOCKET_PING_TIMEOUT = int(os.getenv('WEBSOCKET_PING_TIMEOUT', 60))
    
    # Configuration des graphiques
    MAX_CHART_POINTS = int(os.getenv('MAX_CHART_POINTS', 50))
    CHART_UPDATE_INTERVAL = float(os.getenv('CHART_UPDATE_INTERVAL', 1.0))  # secondes
    
    # CORRECTION: Configuration monitoring de santé
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', 30))  # secondes
    CONNECTION_TIMEOUT_WARNING = int(os.getenv('CONNECTION_TIMEOUT_WARNING', 30))  # secondes
    DATA_QUEUE_MAX_SIZE = int(os.getenv('DATA_QUEUE_MAX_SIZE', 1000))
    
    # Configuration de logging améliorée
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = BASE_DIR / 'logs' / 'neurosity_monitor.log'
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configuration de sécurité
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    RATE_LIMIT = os.getenv('RATE_LIMIT', '100 per minute')
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    
    # CORRECTION: Configuration multiprocessing
    PROCESS_TIMEOUT = int(os.getenv('PROCESS_TIMEOUT', 30))
    QUEUE_TIMEOUT = int(os.getenv('QUEUE_TIMEOUT', 5))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 1))  # Pour les tâches en arrière-plan
    
    # CORRECTION: Configuration des métriques
    SUPPORTED_METRICS = ['calm', 'focus', 'attention', 'brainwaves']
    METRIC_VALIDATION_ENABLED = os.getenv('METRIC_VALIDATION_ENABLED', 'True').lower() == 'true'
    BRAINWAVE_TYPES = ['delta', 'theta', 'alpha', 'beta', 'gamma']
    
    @classmethod
    def validate(cls):
        """Valide la configuration avec vérifications améliorées"""
        errors = []
        warnings = []
        
        # Vérifier les variables Neurosity requises
        if not cls.NEUROSITY_EMAIL:
            errors.append("NEUROSITY_EMAIL manquant dans .env")
        elif '@' not in cls.NEUROSITY_EMAIL:
            warnings.append("NEUROSITY_EMAIL ne semble pas être un email valide")
        
        if not cls.NEUROSITY_PASSWORD:
            errors.append("NEUROSITY_PASSWORD manquant dans .env")
        elif len(cls.NEUROSITY_PASSWORD) < 6:
            warnings.append("NEUROSITY_PASSWORD semble court (moins de 6 caractères)")
        
        if not cls.NEUROSITY_DEVICE_ID:
            errors.append("NEUROSITY_DEVICE_ID manquant dans .env")
        
        # CORRECTION: Vérifications de cohérence des valeurs
        if cls.MAX_SESSION_DURATION <= 0:
            errors.append("MAX_SESSION_DURATION doit être positif")
        
        if cls.MAX_CHART_POINTS <= 0:
            errors.append("MAX_CHART_POINTS doit être positif")
        
        if cls.CHART_UPDATE_INTERVAL <= 0:
            errors.append("CHART_UPDATE_INTERVAL doit être positif")
        
        if cls.HEALTH_CHECK_INTERVAL <= 0:
            errors.append("HEALTH_CHECK_INTERVAL doit être positif")
        
        # Vérifications des limites de sécurité
        if cls.MAX_SESSION_DURATION > 86400:  # 24 heures
            warnings.append("MAX_SESSION_DURATION très élevé (>24h), risque de gros fichiers")
        
        if cls.MAX_CHART_POINTS > 1000:
            warnings.append("MAX_CHART_POINTS très élevé (>1000), peut impacter les performances")
        
        # CORRECTION: Créer les dossiers nécessaires avec gestion d'erreurs
        try:
            cls.DATA_DIRECTORY.mkdir(exist_ok=True, parents=True)
            cls.LOG_FILE.parent.mkdir(exist_ok=True, parents=True)
        except Exception as e:
            errors.append(f"Impossible de créer les dossiers: {e}")
        
        # CORRECTION: Vérifier les permissions d'écriture
        if cls.DATA_DIRECTORY.exists() and not os.access(cls.DATA_DIRECTORY, os.W_OK):
            errors.append(f"Pas de permission d'écriture sur {cls.DATA_DIRECTORY}")
        
        if cls.LOG_FILE.parent.exists() and not os.access(cls.LOG_FILE.parent, os.W_OK):
            warnings.append(f"Pas de permission d'écriture pour les logs: {cls.LOG_FILE.parent}")
        
        # CORRECTION: Validation du niveau de log
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if cls.LOG_LEVEL not in valid_log_levels:
            warnings.append(f"LOG_LEVEL invalide: {cls.LOG_LEVEL}, utilisation de INFO")
            cls.LOG_LEVEL = 'INFO'
        
        # Afficher les avertissements
        if warnings:
            print("⚠️  Avertissements de configuration:")
            for warning in warnings:
                print(f"   - {warning}")
        
        # Lever les erreurs si nécessaire
        if errors:
            error_msg = "❌ Erreurs de configuration:\n" + "\n".join(f"   - {error}" for error in errors)
            raise ValueError(error_msg)
        
        return True
    
    @classmethod
    def get_neurosity_config(cls):
        """Retourne la configuration Neurosity"""
        return {
            'device_id': cls.NEUROSITY_DEVICE_ID,
            'email': cls.NEUROSITY_EMAIL,
            'password': cls.NEUROSITY_PASSWORD
        }
    
    @classmethod
    def get_logging_config(cls):
        """CORRECTION: Retourne la configuration de logging complète"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': cls.LOG_FORMAT
                },
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'level': cls.LOG_LEVEL,
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard'
                },
                'file': {
                    'level': cls.LOG_LEVEL,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': str(cls.LOG_FILE),
                    'maxBytes': cls.LOG_MAX_BYTES,
                    'backupCount': cls.LOG_BACKUP_COUNT,
                    'formatter': 'detailed'
                }
            },
            'loggers': {
                '': {  # Root logger
                    'handlers': ['console', 'file'],
                    'level': cls.LOG_LEVEL,
                    'propagate': False
                }
            }
        }
    
    @classmethod
    def get_flask_config(cls):
        """CORRECTION: Retourne la configuration Flask complète"""
        return {
            'SECRET_KEY': cls.SECRET_KEY,
            'DEBUG': cls.DEBUG,
            'TESTING': False,
            'SESSION_COOKIE_SECURE': cls.SESSION_COOKIE_SECURE,
            'SESSION_COOKIE_HTTPONLY': cls.SESSION_COOKIE_HTTPONLY,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': 3600,  # 1 heure
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max upload
        }
    
    @classmethod
    def get_socketio_config(cls):
        """CORRECTION: Retourne la configuration SocketIO"""
        return {
            'cors_allowed_origins': cls.CORS_ORIGINS,
            'ping_interval': cls.WEBSOCKET_PING_INTERVAL,
            'ping_timeout': cls.WEBSOCKET_PING_TIMEOUT,
            'max_http_buffer_size': 1e6,  # 1MB
            'logger': cls.DEBUG,
            'engineio_logger': cls.DEBUG
        }


class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # CORRECTION: Paramètres de développement plus permissifs
    MAX_SESSION_DURATION = 3600  # 1 heure en dev
    AUTO_CLEANUP_ENABLED = False  # Pas de nettoyage automatique en dev
    METRIC_VALIDATION_ENABLED = True  # Validation stricte en dev


class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # CORRECTION: Sécurité renforcée en production
    SESSION_COOKIE_SECURE = True
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000').split(',')
    RATE_LIMIT = '50 per minute'
    
    # Performances optimisées
    MAX_CHART_POINTS = 30  # Moins de points pour de meilleures performances
    AUTO_CLEANUP_ENABLED = True
    DAYS_TO_KEEP_SESSIONS = 7  # Conservation plus courte en production
    
    @classmethod
    def validate(cls):
        """Validation supplémentaire pour la production"""
        super().validate()
        
        # Vérifications supplémentaires pour la production
        if cls.SECRET_KEY == 'neurosity_monitoring_secret_key_change_in_production':
            raise ValueError("SECRET_KEY par défaut en production - CHANGEZ-LA!")
        
        if '*' in cls.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS trop permissif en production")
        
        return True


class TestingConfig(Config):
    """Configuration pour les tests"""
    DEBUG = True
    TESTING = True
    DATA_DIRECTORY = BASE_DIR / 'test_data'
    CSV_DELIMITER = ','
    LOG_LEVEL = 'DEBUG'
    
    # CORRECTION: Configuration de test spécifique
    MAX_SESSION_DURATION = 60  # 1 minute pour les tests
    MAX_CHART_POINTS = 10
    AUTO_CLEANUP_ENABLED = False
    METRIC_VALIDATION_ENABLED = True
    
    # Pas de fichiers de log en test
    LOG_FILE = BASE_DIR / 'test_logs' / 'test.log'


# CORRECTION: Configuration par défaut selon l'environnement avec fallback
config_mapping = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env_name: str = None):
    """
    Retourne la configuration active avec détection automatique
    
    Args:
        env_name: Nom de l'environnement (optionnel)
    
    Returns:
        Classe de configuration appropriée
    """
    if env_name is None:
        env_name = os.getenv('FLASK_ENV', os.getenv('APP_ENV', 'development'))
    
    config_class = config_mapping.get(env_name, config_mapping['default'])
    
    # Validation de la configuration
    try:
        config_class.validate()
        print(f"✅ Configuration '{env_name}' validée avec succès")
    except ValueError as e:
        print(f"❌ Erreur de configuration '{env_name}': {e}")
        raise
    
    return config_class


def setup_logging(config_class=None):
    """
    CORRECTION: Configure le système de logging
    
    Args:
        config_class: Classe de configuration à utiliser
    """
    if config_class is None:
        config_class = get_config()
    
    try:
        import logging.config
        logging_config = config_class.get_logging_config()
        logging.config.dictConfig(logging_config)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configuré avec niveau: {config_class.LOG_LEVEL}")
        logger.info(f"Fichier de log: {config_class.LOG_FILE}")
        
    except Exception as e:
        # Fallback vers une configuration basique
        logging.basicConfig(
            level=getattr(logging, config_class.LOG_LEVEL, logging.INFO),
            format=config_class.LOG_FORMAT
        )
        logger = logging.getLogger(__name__)
        logger.warning(f"Configuration de logging avancée échouée, utilisation basique: {e}")


def get_app_info():
    """
    CORRECTION: Retourne des informations sur l'application
    
    Returns:
        Dict avec les informations de l'application
    """
    config_class = get_config()
    
    return {
        'app_name': 'Neurosity Crown Monitor',
        'version': '2.0.0-corrected',
        'environment': os.getenv('FLASK_ENV', 'development'),
        'debug': config_class.DEBUG,
        'data_directory': str(config_class.DATA_DIRECTORY),
        'supported_metrics': config_class.SUPPORTED_METRICS,
        'max_session_duration': config_class.MAX_SESSION_DURATION,
        'auto_cleanup': config_class.AUTO_CLEANUP_ENABLED,
        'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
    }


# CORRECTION: Fonction utilitaire pour vérifier l'environnement
def check_environment():
    """
    Vérifie que l'environnement est correctement configuré
    
    Returns:
        bool: True si l'environnement est OK
    """
    try:
        config_class = get_config()
        
        # Vérifier les dépendances Python essentielles
        required_modules = ['flask', 'flask_socketio', 'pandas', 'dotenv']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"❌ Modules Python manquants: {', '.join(missing_modules)}")
            return False
        
        print("✅ Environnement Python validé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification environnement: {e}")
        return False


# CORRECTION: Point d'entrée pour les tests de configuration
if __name__ == "__main__":
    print("🔧 Test de configuration Neurosity Monitor")
    print("=" * 50)
    
    # Tester toutes les configurations
    for env_name in ['development', 'production', 'testing']:
        print(f"\n📋 Test configuration: {env_name}")
        try:
            config = get_config(env_name)
            print(f"   ✅ Configuration '{env_name}' OK")
            
            # Afficher quelques paramètres clés
            print(f"   📊 Données: {config.DATA_DIRECTORY}")
            print(f"   ⏱️  Session max: {config.MAX_SESSION_DURATION}s")
            print(f"   📈 Points chart: {config.MAX_CHART_POINTS}")
            
        except Exception as e:
            print(f"   ❌ Erreur '{env_name}': {e}")
    
    print(f"\n🔍 Vérification environnement:")
    if check_environment():
        print("   ✅ Environnement prêt")
    else:
        print("   ❌ Problèmes détectés")
    
    print(f"\n📱 Informations application:")
    app_info = get_app_info()
    for key, value in app_info.items():
        print(f"   {key}: {value}")
    
    print("\n🎯 Test terminé")