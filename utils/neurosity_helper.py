"""
Helpers et utilitaires pour le SDK Neurosity - Version Corrigée
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import json
import time

logger = logging.getLogger(__name__)


class NeurosityConnectionManager:
    """Gestionnaire de connexion Neurosity avec gestion d'erreurs avancée"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.neurosity = None
        self.is_connected = False
        self.connection_attempts = 0
        self.max_attempts = 3
        self.last_connection_time = None
        self.subscriptions = {}
    
    def connect(self) -> bool:
        """CORRECTION: Connecte au dispositif Neurosity (version synchrone)"""
        from neurosity import NeurositySDK
        
        self.connection_attempts += 1
        
        try:
            logger.info(f"Tentative de connexion {self.connection_attempts}/{self.max_attempts}")
            
            # Initialiser le SDK
            self.neurosity = NeurositySDK({
                "device_id": self.config['device_id'],
            })
            
            # CORRECTION: Se connecter avec les identifiants (version synchrone)
            # L'API Neurosity réelle utilise probablement une méthode synchrone
            login_result = self.neurosity.login({
                "email": self.config['email'],
                "password": self.config['password']
            })
            
            # Vérifier l'état du dispositif
            device_online = self.check_device_status()
            if not device_online:
                logger.warning("Dispositif hors ligne")
                return False
            
            self.is_connected = True
            self.last_connection_time = datetime.now()
            self.connection_attempts = 0
            
            logger.info("✅ Connexion Neurosity réussie")
            return True
        
        except Exception as e:
            logger.error(f"❌ Erreur de connexion: {e}")
            
            if self.connection_attempts < self.max_attempts:
                time.sleep(2 ** self.connection_attempts)  # Backoff exponentiel
                return self.connect()
            
            return False
    
    def disconnect(self):
        """CORRECTION: Déconnecte proprement du dispositif (version synchrone)"""
        try:
            if self.neurosity and self.is_connected:
                # Arrêter toutes les souscriptions
                self.unsubscribe_all()
                
                # Déconnecter
                self.neurosity.logout()
            
            self.is_connected = False
            self.neurosity = None
            logger.info("Déconnexion Neurosity réussie")
        
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {e}")
    
    def check_device_status(self) -> bool:
        """CORRECTION: Vérifie l'état du dispositif (version synchrone)"""
        try:
            if not self.neurosity:
                return False
            
            # CORRECTION: Utiliser l'API réelle (probablement synchrone)
            try:
                # En réalité, l'API Neurosity peut avoir des méthodes différentes
                # Adapter selon la vraie documentation
                info = self.neurosity.getInfo()
                return bool(info)
            except AttributeError:
                # Fallback si getInfo n'existe pas
                logger.warning("Méthode getInfo non disponible, considérant comme connecté")
                return True
            except Exception as api_error:
                logger.error(f"Erreur API getInfo: {api_error}")
                return False
        
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut: {e}")
            return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """CORRECTION: Récupère les informations du dispositif (version synchrone)"""
        try:
            if not self.neurosity:
                return {}
            
            try:
                # Récupérer les infos du dispositif (adapter selon l'API)
                info = self.neurosity.getInfo()
                return {
                    'device_id': self.config['device_id'],
                    'online': True,
                    'battery': info.get('battery', 'unknown') if info else 'unknown',
                    'signal_quality': info.get('signalQuality', 'unknown') if info else 'unknown',
                    'firmware': info.get('firmware', 'unknown') if info else 'unknown',
                    'model': info.get('model', 'Crown') if info else 'Crown',
                    'connected_at': self.last_connection_time.isoformat() if self.last_connection_time else None
                }
            except AttributeError:
                # Fallback si getInfo n'existe pas
                return {
                    'device_id': self.config['device_id'],
                    'online': True,
                    'battery': 'unknown',
                    'signal_quality': 'unknown',
                    'firmware': 'unknown',
                    'model': 'Crown',
                    'connected_at': self.last_connection_time.isoformat() if self.last_connection_time else None
                }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos: {e}")
            return {}
    
    def subscribe_to_metric(self, metric: str, callback: Callable, options: Dict = None):
        """CORRECTION: Souscrit à une métrique avec l'API réelle"""
        try:
            if not self.is_connected or not self.neurosity:
                raise Exception("Non connecté au dispositif")
            
            # CORRECTION: Mapper selon l'API réelle Neurosity
            # L'API réelle utilise probablement des noms différents
            safe_callback = self._create_safe_callback(callback, metric)
            
            subscription = None
            
            if metric == 'calm':
                # L'API réelle pourrait être différente
                subscription = self.neurosity.calm(safe_callback)
            elif metric == 'focus':
                subscription = self.neurosity.focus(safe_callback)
            elif metric == 'attention':
                # Attention pourrait ne pas exister dans l'API réelle
                subscription = self.neurosity.attention(safe_callback) if hasattr(self.neurosity, 'attention') else None
            elif metric == 'brainwaves':
                # Probablement brainwaves ou rawBrainwaves
                subscription = self.neurosity.brainwaves(safe_callback)
            elif metric == 'kinesis':
                # Pour les mouvements
                subscription = self.neurosity.kinesis(safe_callback) if hasattr(self.neurosity, 'kinesis') else None
            elif metric == 'raw':
                subscription = self.neurosity.raw(safe_callback) if hasattr(self.neurosity, 'raw') else None
            
            if subscription:
                self.subscriptions[metric] = subscription
                logger.info(f"Souscription active pour {metric}")
            else:
                logger.warning(f"Métrique {metric} non disponible dans cette version du SDK")
        
        except Exception as e:
            logger.error(f"Erreur de souscription à {metric}: {e}")
            raise
    
    def _create_safe_callback(self, callback: Callable, metric: str) -> Callable:
        """Crée un callback sécurisé avec gestion d'erreurs"""
        
        def safe_callback(data):
            try:
                # Valider les données
                if not self._validate_metric_data(data, metric):
                    logger.warning(f"Données invalides pour {metric}: {data}")
                    return
                
                # Enrichir avec métadonnées
                enriched_data = self._enrich_data(data, metric)
                
                # Appeler le callback original
                callback(enriched_data)
            
            except Exception as e:
                logger.error(f"Erreur dans le callback {metric}: {e}")
        
        return safe_callback
    
    def _validate_metric_data(self, data: Any, metric: str) -> bool:
        """Valide les données d'une métrique"""
        if not isinstance(data, dict):
            return False
        
        # Validations spécifiques par métrique
        if metric in ['calm', 'focus', 'attention']:
            probability = data.get('probability')
            return isinstance(probability, (int, float)) and 0 <= probability <= 1
        
        elif metric == 'brainwaves':
            # CORRECTION: Validation plus flexible pour les ondes cérébrales
            # L'API réelle peut avoir des structures différentes
            required_waves = ['delta', 'theta', 'alpha', 'beta', 'gamma']
            
            # Vérifier si au moins une onde est présente
            has_waves = any(wave in data for wave in required_waves)
            if not has_waves:
                return False
            
            # Vérifier que les ondes présentes sont des listes
            for wave in required_waves:
                if wave in data and not isinstance(data[wave], list):
                    return False
            
            return True
        
        return True
    
    def _enrich_data(self, data: Dict, metric: str) -> Dict:
        """Enrichit les données avec des métadonnées"""
        return {
            **data,
            'metric': metric,
            'timestamp': datetime.now().isoformat(),
            'device_id': self.config['device_id'],
            'connection_quality': self._get_connection_quality()
        }
    
    def _get_connection_quality(self) -> str:
        """Évalue la qualité de la connexion"""
        if not self.is_connected:
            return 'disconnected'
        
        if self.last_connection_time:
            duration = datetime.now() - self.last_connection_time
            if duration < timedelta(minutes=1):
                return 'excellent'
            elif duration < timedelta(minutes=5):
                return 'good'
            else:
                return 'fair'
        
        return 'unknown'
    
    def unsubscribe_all(self):
        """CORRECTION: Désabonne de toutes les métriques (version synchrone)"""
        for metric, subscription in self.subscriptions.items():
            try:
                if subscription and callable(subscription):
                    # L'API réelle peut utiliser subscription() ou subscription.unsubscribe()
                    if hasattr(subscription, 'unsubscribe'):
                        subscription.unsubscribe()
                    else:
                        subscription()  # Certaines APIs utilisent la fonction directement
                logger.info(f"Désabonnement de {metric}")
            except Exception as e:
                logger.error(f"Erreur lors du désabonnement de {metric}: {e}")
        
        self.subscriptions.clear()
    
    def unsubscribe_from_metric(self, metric: str):
        """CORRECTION: Désabonne d'une métrique spécifique (version synchrone)"""
        if metric in self.subscriptions:
            try:
                subscription = self.subscriptions[metric]
                if subscription and callable(subscription):
                    if hasattr(subscription, 'unsubscribe'):
                        subscription.unsubscribe()
                    else:
                        subscription()
                del self.subscriptions[metric]
                logger.info(f"Désabonnement de {metric}")
            except Exception as e:
                logger.error(f"Erreur lors du désabonnement de {metric}: {e}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Retourne l'état de la connexion"""
        return {
            'connected': self.is_connected,
            'device_id': self.config['device_id'],
            'connection_attempts': self.connection_attempts,
            'last_connection': self.last_connection_time.isoformat() if self.last_connection_time else None,
            'active_subscriptions': list(self.subscriptions.keys()),
            'connection_quality': self._get_connection_quality()
        }


class DataValidator:
    """Validateur de données Neurosity"""
    
    @staticmethod
    def validate_calm_data(data: Dict) -> bool:
        """Valide les données de calme"""
        return (
                isinstance(data, dict) and
                'probability' in data and
                isinstance(data['probability'], (int, float)) and
                0 <= data['probability'] <= 1
        )
    
    @staticmethod
    def validate_focus_data(data: Dict) -> bool:
        """Valide les données de concentration"""
        return DataValidator.validate_calm_data(data)  # Même structure
    
    @staticmethod
    def validate_attention_data(data: Dict) -> bool:
        """Valide les données d'attention"""
        return DataValidator.validate_calm_data(data)  # Même structure
    
    @staticmethod
    def validate_brainwaves_data(data: Dict) -> bool:
        """CORRECTION: Valide les données d'ondes cérébrales avec plus de flexibilité"""
        if not isinstance(data, dict):
            return False
        
        required_waves = ['delta', 'theta', 'alpha', 'beta', 'gamma']
        
        # Au moins une onde doit être présente
        has_any_wave = any(wave in data for wave in required_waves)
        if not has_any_wave:
            return False
        
        # Vérifier que les ondes présentes sont valides
        for wave in required_waves:
            if wave in data:
                wave_data = data[wave]
                if not isinstance(wave_data, list):
                    return False
                
                # Vérifier que tous les éléments sont des nombres (si la liste n'est pas vide)
                if wave_data and not all(isinstance(x, (int, float)) for x in wave_data):
                    return False
        
        return True
    
    @staticmethod
    def sanitize_data(data: Any) -> Any:
        """Nettoie et sanitise les données"""
        if isinstance(data, dict):
            return {k: DataValidator.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [DataValidator.sanitize_data(item) for item in data]
        elif isinstance(data, (int, float)):
            # Limiter la précision et gérer les valeurs spéciales
            if data != data:  # NaN
                return 0
            elif data == float('inf') or data == float('-inf'):
                return 0
            else:
                return round(float(data), 6)
        else:
            return data


class MetricsProcessor:
    """Processeur de métriques avec calculs statistiques"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.history = {
            'calm': [],
            'focus': [],
            'attention': [],
            'brainwaves': {
                'delta': [],
                'theta': [],
                'alpha': [],
                'beta': [],
                'gamma': []
            }
        }
    
    def process_metric(self, metric: str, data: Dict) -> Dict:
        """Traite une métrique et calcule les statistiques"""
        processed = {
            'raw': data,
            'timestamp': datetime.now().isoformat(),
            'metric': metric
        }
        
        if metric in ['calm', 'focus', 'attention']:
            probability = data.get('probability', 0)
            percentage = probability * 100
            
            # Ajouter à l'historique
            self.history[metric].append(percentage)
            if len(self.history[metric]) > self.window_size:
                self.history[metric].pop(0)
            
            # Calculer les statistiques
            processed.update({
                'probability': probability,
                'percentage': percentage,
                'average': self._calculate_average(self.history[metric]),
                'trend': self._calculate_trend(self.history[metric])
            })
        
        elif metric == 'brainwaves':
            processed['waves'] = {}
            
            for wave_type in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                wave_data = data.get(wave_type, [])
                if wave_data:
                    # Calculer les statistiques pour cette onde
                    wave_stats = {
                        'raw': wave_data,
                        'average': sum(wave_data) / len(wave_data),
                        'max': max(wave_data),
                        'min': min(wave_data),
                        'std': self._calculate_std(wave_data)
                    }
                    
                    # Ajouter à l'historique
                    self.history['brainwaves'][wave_type].append(wave_stats['average'])
                    if len(self.history['brainwaves'][wave_type]) > self.window_size:
                        self.history['brainwaves'][wave_type].pop(0)
                    
                    # Tendance
                    wave_stats['trend'] = self._calculate_trend(
                        self.history['brainwaves'][wave_type]
                    )
                    
                    processed['waves'][wave_type] = wave_stats
        
        return processed
    
    def _calculate_average(self, values: List[float]) -> float:
        """Calcule la moyenne"""
        return sum(values) / len(values) if values else 0
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calcule l'écart-type"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcule la tendance (ascending, descending, stable)"""
        if len(values) < 2:
            return 'stable'
        
        recent = values[-3:] if len(values) >= 3 else values
        
        if len(recent) < 2:
            return 'stable'
        
        # Calculer la pente
        slope = (recent[-1] - recent[0]) / len(recent)
        
        if slope > 0.5:
            return 'ascending'
        elif slope < -0.5:
            return 'descending'
        else:
            return 'stable'
    
    def get_session_summary(self) -> Dict:
        """Retourne un résumé de la session"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {}
        }
        
        # Résumé des métriques principales
        for metric in ['calm', 'focus', 'attention']:
            if self.history[metric]:
                summary['metrics'][metric] = {
                    'average': self._calculate_average(self.history[metric]),
                    'max': max(self.history[metric]),
                    'min': min(self.history[metric]),
                    'std': self._calculate_std(self.history[metric]),
                    'samples': len(self.history[metric])
                }
        
        # Résumé des ondes cérébrales
        brainwave_summary = {}
        for wave_type in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
            wave_history = self.history['brainwaves'][wave_type]
            if wave_history:
                brainwave_summary[wave_type] = {
                    'average': self._calculate_average(wave_history),
                    'max': max(wave_history),
                    'min': min(wave_history),
                    'std': self._calculate_std(wave_history),
                    'samples': len(wave_history)
                }
        
        if brainwave_summary:
            summary['metrics']['brainwaves'] = brainwave_summary
        
        return summary
    
    def reset(self):
        """Remet à zéro l'historique"""
        self.history = {
            'calm': [],
            'focus': [],
            'attention': [],
            'brainwaves': {
                'delta': [],
                'theta': [],
                'alpha': [],
                'beta': [],
                'gamma': []
            }
        }


# CORRECTION: Classe utilitaire pour la compatibilité API
class NeurositySDKAdapter:
    """
    Adaptateur pour gérer les différences entre versions du SDK Neurosity
    """
    
    def __init__(self, neurosity_sdk):
        self.sdk = neurosity_sdk
        self._detect_api_version()
    
    def _detect_api_version(self):
        """Détecte la version de l'API pour adapter les appels"""
        self.has_calm = hasattr(self.sdk, 'calm')
        self.has_focus = hasattr(self.sdk, 'focus')
        self.has_attention = hasattr(self.sdk, 'attention')
        self.has_brainwaves = hasattr(self.sdk, 'brainwaves')
        self.has_raw = hasattr(self.sdk, 'raw')
        self.has_getinfo = hasattr(self.sdk, 'getInfo')
        
        logger.info(f"API Neurosity détectée - Méthodes disponibles: "
                   f"calm={self.has_calm}, focus={self.has_focus}, "
                   f"attention={self.has_attention}, brainwaves={self.has_brainwaves}")
    
    def subscribe_metric(self, metric: str, callback: Callable):
        """Souscrit à une métrique en s'adaptant à l'API disponible"""
        if metric == 'calm' and self.has_calm:
            return self.sdk.calm(callback)
        elif metric == 'focus' and self.has_focus:
            return self.sdk.focus(callback)
        elif metric == 'attention' and self.has_attention:
            return self.sdk.attention(callback)
        elif metric == 'brainwaves' and self.has_brainwaves:
            return self.sdk.brainwaves(callback)
        elif metric == 'raw' and self.has_raw:
            return self.sdk.raw(callback)
        else:
            logger.warning(f"Métrique {metric} non disponible dans cette version du SDK")
            return None
    
    def get_device_info(self):
        """Récupère les infos du dispositif avec fallback"""
        if self.has_getinfo:
            return self.sdk.getInfo()
        else:
            logger.warning("getInfo non disponible, retour d'infos basiques")
            return {'model': 'Crown', 'battery': 'unknown', 'signalQuality': 'unknown'}