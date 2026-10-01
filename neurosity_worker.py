#!/usr/bin/env python3
"""
NEUROSITY WORKER PROCESS - FICHIER SÉPARÉ POUR PYINSTALLER
Ce fichier contient uniquement le processus Neurosity pour éviter les problèmes de multiprocessing
"""

import time
import logging
from datetime import datetime
from queue import Empty

logger = logging.getLogger(__name__)


def neurosity_process(command_queue, data_queue, response_queue):
    """
    Processus séparé pour gérer le SDK Neurosity.
    IMPORTANT: Ce fichier est séparé pour que PyInstaller puisse le trouver correctement.
    """
    logger.info("[WORKER] Démarrage du processus Neurosity...")
    
    try:
        from neurosity import NeurositySDK
    except ImportError:
        logger.error("[WORKER] SDK Neurosity non installé")
        response_queue.put({
            'success': False,
            'error': 'SDK Neurosity non installe. Installez-le avec: pip install neurosity', 'code': 'sdk_missing'
        })
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
    
    def cleanup():
        nonlocal neurosity, is_monitoring, subscriptions, is_connected, battery_subscription
        
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
        try:
            message = {
                'type': data_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'device_status': device_status.copy()
            }
            data_queue.put(message)
        except Exception as e:
            logger.error(f"[WORKER] Erreur send_data: {e}")
    
    def detect_device():
        logger.info("[WORKER] Détection du casque...")
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
            
            for i in range(100):
                if all(data_received.values()):
                    logger.info("[WORKER] Casque détecté et opérationnel!")
                    return True
                time.sleep(0.1)
            
            logger.warning("[WORKER] Pas de données reçues du casque")
            return False
        finally:
            for sub in test_subs:
                if callable(sub):
                    try:
                        sub()
                    except:
                        pass
    
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
        """Traite les données d'ondes cérébrales - RENVOIE 8 VALEURS PAR BANDE"""
        try:
            if not data or 'data' not in data:
                logger.warning("[WORKER] Données brainwaves vides")
                return
            
            bands_data = data['data']
            result = {}
            
            # Pour chaque bande d'ondes, conserver toutes les 8 valeurs (une par électrode)
            for wave in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                if wave in bands_data:
                    values = bands_data[wave]
                    if isinstance(values, list) and len(values) == 8:
                        # Conserver toutes les 8 valeurs (pas de moyenne ici !)
                        result[wave] = [
                            round(v, 3) if isinstance(v, (int, float)) and v >= 0 else 0
                            for v in values
                        ]
                        logger.debug(f"[WORKER] {wave}: {result[wave][:2]}... (8 valeurs)")
                    else:
                        # Si format incorrect, mettre 8 zéros
                        logger.warning(
                            f"[WORKER] Format incorrect pour {wave}: {type(values)}, len={len(values) if isinstance(values, list) else 'N/A'}")
                        result[wave] = [0] * 8
                else:
                    # Si pas de données pour cette bande, mettre 8 zéros
                    logger.warning(f"[WORKER] Bande {wave} absente")
                    result[wave] = [0] * 8
            
            result['timestamp'] = time.time() * 1000
            
            # Log pour vérifier que les données sont bien envoyées
            logger.debug(f"[WORKER] Envoi brainwaves: delta={len(result.get('delta', []))} valeurs")
            
            send_data('brainwaves', result)
        
        except Exception as e:
            logger.error(f"[WORKER] Erreur brainwaves: {e}")
            import traceback
            traceback.print_exc()
    
    def signal_quality_callback(data):
        """Traite la qualité du signal des électrodes"""
        try:
            # Log pour voir le format exact des données reçues
            logger.debug(f"[WORKER] Signal quality brut: {data}")
            
            if not data:
                logger.warning("[WORKER] Données signal quality vides")
                return
            
            # Le SDK Neurosity envoie un tableau de 8 objets (un par électrode)
            if isinstance(data, list) and len(data) == 8:
                electrodes = ['CP3', 'C3', 'F5', 'PO3', 'PO4', 'F6', 'C4', 'CP4']
                signal_dict = {}
                
                for i in range(min(len(data), len(electrodes))):
                    electrode_data = data[i]
                    
                    if isinstance(electrode_data, dict):
                        # Format attendu : {'status': 'great/good/bad/noContact', 'standardDeviation': number}
                        status = electrode_data.get('status', 'noContact')
                        std_dev = electrode_data.get('standardDeviation', 0)
                        
                        signal_dict[electrodes[i]] = {
                            'status': status,
                            'standardDeviation': round(std_dev, 3) if isinstance(std_dev, (int, float)) else 0
                        }
                        
                        logger.debug(f"[WORKER] {electrodes[i]}: status={status}, stdDev={std_dev}")
                    else:
                        # Format inattendu
                        logger.warning(f"[WORKER] Format inattendu pour {electrodes[i]}: {type(electrode_data)}")
                        signal_dict[electrodes[i]] = {
                            'status': 'noContact',
                            'standardDeviation': 0
                        }
                
                logger.debug(f"[WORKER] Envoi signal_quality: {list(signal_dict.keys())}")
                send_data('signal_quality', signal_dict)
            else:
                logger.warning(
                    f"[WORKER] Format signal quality incorrect: {type(data)}, len={len(data) if isinstance(data, list) else 'N/A'}")
        
        except Exception as e:
            logger.error(f"[WORKER] Erreur signal quality: {e}")
            import traceback
            traceback.print_exc()
    
    def battery_callback(status):
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
            logger.error(f"[WORKER] Erreur battery: {e}")
    
    def brainwaves_raw_callback(data):
        if data:
            send_data('brainwaves_raw', data)
    
    # Boucle principale du processus worker
    logger.info("[WORKER] Boucle principale démarrée")
    
    while True:
        try:
            command = command_queue.get(timeout=1)
            action = command.get('action')
            
            if action == 'connect':
                logger.info("[WORKER] Commande de connexion reçue...")
                try:
                    credentials = command.get('credentials', {})
                    device_id = credentials.get('device_id')
                    email = credentials.get('email')
                    password = credentials.get('password')
                    
                    if not all([device_id, email, password]):
                        response_queue.put({
                            'success': False,
                            'error': 'Configuration manquante.', 'code': 'missing_config'
                        })
                        continue
                    
                    logger.info(f"[WORKER] Connexion avec device_id: {device_id[:8]}...")
                    
                    neurosity = NeurositySDK({"device_id": device_id})
                    neurosity.login({"email": email, "password": password})
                    
                    logger.info("[WORKER] Login réussi, détection du casque...")
                    
                    if detect_device():
                        is_connected = True
                        device_status['online'] = True
                        device_status['signal'] = 'excellent'
                        
                        try:
                            initial_status = neurosity.status()
                            if isinstance(initial_status, dict):
                                device_status['battery'] = int(round(initial_status.get('battery', 0)))
                                device_status['charging'] = initial_status.get('charging', False)
                        except:
                            pass
                        
                        battery_subscription = neurosity.status(battery_callback)
                        
                        logger.info("[WORKER] Casque connecté avec succès!")
                        response_queue.put({
                            'success': True,
                            'connected': True,
                            'device_status': device_status,
                            'message': 'Casque Neurosity connecte!', 'code': 'device_connected'
                        })
                    else:
                        cleanup()
                        response_queue.put({
                            'success': False,
                            'error': 'Casque non detecte.', 'code': 'device_not_detected'
                        })
                
                except Exception as e:
                    cleanup()
                    error_msg = str(e)
                    logger.error(f"[WORKER] Erreur connexion: {error_msg}")
                    response_queue.put({'success': False, 'error': error_msg})
            
            elif action == 'start_monitoring':
                if not is_connected:
                    response_queue.put({'success': False, 'error': 'Non connecte', 'code': 'not_connected'})
                    continue
                
                if not is_monitoring:
                    logger.info("[WORKER] Démarrage monitoring...")
                    
                    subscriptions = [
                        neurosity.calm(create_metric_callback('calm')),
                        neurosity.focus(create_metric_callback('focus')),
                        neurosity.brainwaves_power_by_band(brainwaves_callback),
                        neurosity.signal_quality(signal_quality_callback),
                        neurosity.brainwaves_raw(brainwaves_raw_callback)
                    ]
                    
                    is_monitoring = True
                    logger.info("[WORKER] Monitoring actif")
                
                response_queue.put({'success': True, 'monitoring': True})
            
            elif action == 'stop_monitoring':
                if subscriptions:
                    for sub in subscriptions:
                        if callable(sub):
                            try:
                                sub()
                            except:
                                pass
                    subscriptions = []
                is_monitoring = False
                response_queue.put({'success': True, 'monitoring': False})
            
            elif action == 'disconnect':
                cleanup()
                device_status = {
                    'online': False,
                    'battery': 0,
                    'charging': False,
                    'signal': 'disconnected'
                }
                response_queue.put({'success': True, 'connected': False})
            
            elif action == 'quit':
                logger.info("[WORKER] Commande quit reçue")
                break
        
        except Empty:
            continue
        except Exception as e:
            logger.error(f"[WORKER] Erreur dans la boucle: {e}")
            import traceback
            traceback.print_exc()
    
    cleanup()
    logger.info("[WORKER] Processus terminé proprement")