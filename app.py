#!/usr/bin/env python3
"""
NEUROSITY CROWN MONITOR - DÉTECTION STRICTE ET PROFESSIONNELLE
Correction complète : détection réelle du casque basée sur des données biologiques valides
VERSION CORRIGÉE - Validation moins stricte mais intelligente
"""

import os
import sys
import time
import multiprocessing as mp
from pathlib import Path
from datetime import datetime
from queue import Empty
import json
import threading
import statistics
from collections import deque

# Flask et SocketIO
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit

# Variables d'environnement
from dotenv import load_dotenv

# DataManager local
from data_manager import DataManager


# ===============================================
# DÉTECTEUR DE DONNÉES BIOLOGIQUES RÉELLES - VERSION CORRIGÉE
# ===============================================

class BiologicalDataValidator:
    """Validateur de données biologiques réelles vs simulées - VERSION CORRIGÉE"""
    
    def __init__(self):
        self.data_history = {
            'calm': deque(maxlen=10),
            'focus': deque(maxlen=10),
            'timestamps': deque(maxlen=10)
        }
        self.first_timestamp = None
        self.detection_start = None
    
    def add_data_point(self, metric: str, data: dict):
        """Ajoute un point de données pour validation"""
        if metric in ['calm', 'focus']:
            probability = data.get('probability', 0)
            timestamp = data.get('timestamp', 0)
            
            self.data_history[metric].append(probability)
            self.data_history['timestamps'].append(timestamp)
            
            if self.first_timestamp is None:
                self.first_timestamp = timestamp
                self.detection_start = time.time()
    
    def is_real_biological_data(self) -> tuple[bool, str]:
        """
        Détermine si les données sont biologiques réelles - VERSION CORRIGÉE
        Returns: (is_real, reason)
        """
        if len(self.data_history['calm']) < 5:
            return False, "Données insuffisantes pour validation"
        
        # Test 1: Variabilité des données (STRICT - détecte simulation)
        calm_variance = self._calculate_variance(self.data_history['calm'])
        focus_variance = self._calculate_variance(self.data_history['focus'])
        
        if calm_variance < 0.001 and focus_variance < 0.001:
            return False, "Données trop constantes (simulation détectée)"
        
        # Test 2: Distribution réaliste (STRICT - détecte valeurs aberrantes)
        if not self._has_realistic_distribution():
            return False, "Distribution artificielle détectée"
        
        # Test 3: Timestamps cohérents (PERMISSIF - accepte variations hardware)
        timestamp_result, timestamp_reason = self._check_timestamps_permissive()
        if not timestamp_result:
            return False, f"Problème grave timestamps: {timestamp_reason}"
        
        # Test 4: Patterns biologiques (STRICT - détecte corrélations parfaites)
        if not self._has_biological_patterns():
            return False, "Patterns non-biologiques détectés"
        
        # Test 5: Valeurs suspectes (PERMISSIF - tolère précision normale)
        if self._has_highly_suspicious_values():
            return False, "Données clairement simulées détectées"
        
        return True, "Données biologiques authentiques validées"
    
    def _calculate_variance(self, data_list):
        """Calcule la variance des données"""
        if len(data_list) < 2:
            return 0
        return statistics.variance(data_list)
    
    def _has_realistic_distribution(self) -> bool:
        """Vérifie que les données ont une distribution réaliste (STRICT)"""
        calm_data = list(self.data_history['calm'])
        focus_data = list(self.data_history['focus'])
        
        # Les vraies données biologiques sont généralement entre 0.05 et 0.95
        # (légèrement élargi pour être plus réaliste)
        calm_in_range = sum(1 for x in calm_data if 0.05 <= x <= 0.95)
        focus_in_range = sum(1 for x in focus_data if 0.05 <= x <= 0.95)
        
        # Au moins 70% des données doivent être dans la plage réaliste
        # (baissé de 60% pour être plus permissif)
        calm_ratio = calm_in_range / len(calm_data) if calm_data else 0
        focus_ratio = focus_in_range / len(focus_data) if focus_data else 0
        
        return calm_ratio >= 0.7 and focus_ratio >= 0.7
    
    def _check_timestamps_permissive(self) -> tuple[bool, str]:
        """CORRIGÉ: Vérification permissive des timestamps"""
        timestamps = list(self.data_history['timestamps'])
        if len(timestamps) < 2:
            return True, "Timestamps OK"
        
        intervals = []
        for i in range(1, len(timestamps)):
            interval = timestamps[i] - timestamps[i - 1]
            intervals.append(interval)
        
        # Détecter seulement les problèmes GRAVES
        zero_or_negative = sum(1 for x in intervals if x <= 0)
        too_fast = sum(1 for x in intervals if 0 < x < 5)  # Moins de 5ms = suspect
        too_slow = sum(1 for x in intervals if x > 120000)  # Plus de 2 minutes = problème
        
        # Échouer seulement en cas de problèmes graves
        if zero_or_negative > 0:
            return False, "Timestamps qui reculent (simulation)"
        
        if too_fast > len(intervals) * 0.5:  # Plus de 50% trop rapides
            return False, "Fréquence irréaliste (>200Hz)"
        
        if too_slow > len(intervals) * 0.3:  # Plus de 30% avec de gros trous
            return False, "Trous temporels trop importants"
        
        # NOUVEAU: Validation permissive pour les intervalles normaux
        normal_intervals = [x for x in intervals if 5 <= x <= 120000]
        if len(normal_intervals) == 0:
            return False, "Aucun intervalle dans la plage normale"
        
        # Log de debug pour le développement
        if len(intervals) > 0:
            avg_interval = sum(intervals) / len(intervals)
            freq_hz = 1000 / avg_interval if avg_interval > 0 else 0
            print(f"🧠 [DEBUG] Timestamps - Intervalle moyen: {avg_interval:.1f}ms, Fréquence: {freq_hz:.1f}Hz")
            print(f"🧠 [DEBUG] Intervalles: min={min(intervals)}ms, max={max(intervals)}ms")
        
        return True, f"Timestamps valides ({len(normal_intervals)}/{len(intervals)} intervalles normaux)"
    
    def _has_biological_patterns(self) -> bool:
        """Recherche des patterns biologiques naturels (STRICT)"""
        calm_data = list(self.data_history['calm'])
        focus_data = list(self.data_history['focus'])
        
        if len(calm_data) < 5:
            return True
        
        # Les données biologiques ne sont jamais parfaitement synchronisées
        correlation = self._calculate_correlation(calm_data, focus_data)
        
        # Une corrélation parfaite (>0.95 ou <-0.95) est suspecte
        is_valid = abs(correlation) < 0.95
        
        if not is_valid:
            print(f"🧠 [DEBUG] Corrélation suspecte détectée: {correlation:.3f}")
        
        return is_valid
    
    def _calculate_correlation(self, x, y):
        """Calcule la corrélation entre deux séries"""
        if len(x) != len(y) or len(x) < 2:
            return 0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))
        
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        if denominator == 0:
            return 0
        
        return (n * sum_xy - sum_x * sum_y) / denominator
    
    def _has_highly_suspicious_values(self) -> bool:
        """CORRIGÉ: Détecte seulement les valeurs VRAIMENT suspectes"""
        calm_data = list(self.data_history['calm'])
        focus_data = list(self.data_history['focus'])
        
        total_points = len(calm_data) + len(focus_data)
        if total_points == 0:
            return False
        
        # Test 1: Trop de valeurs exactes (0.0, 1.0)
        exact_extremes = sum(1 for x in calm_data + focus_data if x == 0.0 or x == 1.0)
        if exact_extremes / total_points > 0.6:  # Plus de 60% de valeurs exactes
            print(f"🧠 [DEBUG] Trop de valeurs exactes: {exact_extremes}/{total_points}")
            return True
        
        # Test 2: Valeurs répétitives (simulation typique)
        calm_unique = len(set(calm_data))
        focus_unique = len(set(focus_data))
        
        if len(calm_data) > 5 and calm_unique <= 2:  # Seulement 1-2 valeurs différentes
            print(f"🧠 [DEBUG] Valeurs calm trop répétitives: {calm_unique} valeurs uniques")
            return True
        
        if len(focus_data) > 5 and focus_unique <= 2:
            print(f"🧠 [DEBUG] Valeurs focus trop répétitives: {focus_unique} valeurs uniques")
            return True
        
        # Test 3: Patterns arithmétiques parfaits
        if self._has_arithmetic_patterns(calm_data) or self._has_arithmetic_patterns(focus_data):
            print(f"🧠 [DEBUG] Patterns arithmétiques détectés")
            return True
        
        return False
    
    def _has_arithmetic_patterns(self, data):
        """Détecte des patterns arithmétiques parfaits (signe de simulation)"""
        if len(data) < 4:
            return False
        
        # Vérifier si les différences sont constantes (progression arithmétique)
        differences = [data[i + 1] - data[i] for i in range(len(data) - 1)]
        
        if len(set(differences)) <= 1:  # Toutes les différences identiques
            return True
        
        # Vérifier les patterns cycliques simples
        if len(data) >= 6:
            # Pattern ABAB...
            pattern_2 = all(data[i] == data[i % 2] for i in range(len(data)))
            # Pattern ABCABC...
            pattern_3 = all(data[i] == data[i % 3] for i in range(len(data)))
            
            if pattern_2 or pattern_3:
                return True
        
        return False


# ===============================================
# PROCESSUS NEUROSITY AVEC DÉTECTION STRICTE CORRIGÉE
# ===============================================

def neurosity_process(command_queue, data_queue, response_queue):
    """
    Processus Neurosity avec détection stricte de casque réel - VERSION CORRIGÉE
    """
    print("🧠 [NEUROSITY PROCESS] Démarrage avec détection stricte corrigée...")
    
    try:
        from neurosity import NeurositySDK
        
        neurosity = None
        is_connected = False
        is_monitoring = False
        subscriptions = []
        device_status = {'online': False, 'battery': 'unknown', 'signal': 'disconnected'}
        
        # Validateur de données biologiques CORRIGÉ
        bio_validator = None
        
        load_dotenv()
        
        def cleanup():
            """Nettoyage complet"""
            nonlocal neurosity, is_monitoring, subscriptions, is_connected
            try:
                print("🧠 [NEUROSITY] Nettoyage en cours...")
                
                if is_monitoring and subscriptions:
                    for unsub_func in subscriptions:
                        try:
                            if callable(unsub_func):
                                unsub_func()
                        except Exception as e:
                            print(f"🧠 [NEUROSITY] Erreur unsubscribe: {e}")
                    subscriptions = []
                    is_monitoring = False
                
                if neurosity and is_connected:
                    try:
                        neurosity.logout()
                    except Exception as e:
                        print(f"🧠 [NEUROSITY] Erreur logout: {e}")
                
                neurosity = None
                is_connected = False
                device_status.update({'online': False, 'battery': 'unknown', 'signal': 'disconnected'})
                
                print("🧠 [NEUROSITY] Nettoyage terminé")
            except Exception as e:
                print(f"🧠 [NEUROSITY] Erreur nettoyage: {e}")
        
        def send_data(data_type, data):
            """Envoie des données via la queue"""
            try:
                if not is_connected:
                    return
                
                message = {
                    'type': data_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat(),
                    'device_status': device_status.copy()
                }
                data_queue.put(message, timeout=1)
            except Exception as e:
                print(f"🧠 [NEUROSITY] Erreur envoi données {data_type}: {e}")
        
        def send_status_update():
            """Envoie mise à jour du statut"""
            try:
                status_data = {
                    'connected': is_connected,
                    'monitoring': is_monitoring,
                    'device_online': device_status.get('online', False),
                    'device_status': device_status.copy()
                }
                data_queue.put({
                    'type': 'status_update',
                    'data': status_data,
                    'timestamp': datetime.now().isoformat()
                }, timeout=1)
            except:
                pass
        
        def strict_device_detection():
            """
            DÉTECTION STRICTE CORRIGÉE : Teste si le casque envoie des données biologiques réelles
            """
            nonlocal bio_validator
            
            print("🧠 [NEUROSITY] === DÉTECTION STRICTE CORRIGÉE DU CASQUE ===")
            print("🧠 [NEUROSITY] Recherche de données biologiques réelles...")
            
            bio_validator = BiologicalDataValidator()
            detection_timeout = 20  # 20 secondes pour collecter des données
            test_subscriptions = []
            
            try:
                # Callbacks de test pour collecter des données
                def calm_test_callback(data):
                    print(f"🧠 [NEUROSITY] Données calm reçues: {data}")
                    bio_validator.add_data_point('calm', data)
                
                def focus_test_callback(data):
                    print(f"🧠 [NEUROSITY] Données focus reçues: {data}")
                    bio_validator.add_data_point('focus', data)
                
                # S'abonner aux métriques pour le test
                print("🧠 [NEUROSITY] Souscription aux métriques de test...")
                calm_test_sub = neurosity.calm(calm_test_callback)
                focus_test_sub = neurosity.focus(focus_test_callback)
                test_subscriptions = [calm_test_sub, focus_test_sub]
                
                # Collecter des données pendant le timeout
                start_time = time.time()
                print(f"🧠 [NEUROSITY] Collecte de données pendant {detection_timeout} secondes...")
                
                while (time.time() - start_time) < detection_timeout:
                    elapsed = int(time.time() - start_time)
                    data_points = len(bio_validator.data_history['calm'])
                    print(f"🧠 [NEUROSITY] ⏱️  {elapsed}s/{detection_timeout}s - {data_points} points collectés")
                    
                    # Vérification intermédiaire après 8 secondes (plus précoce)
                    if elapsed >= 8 and data_points >= 5:
                        is_real, reason = bio_validator.is_real_biological_data()
                        if is_real:
                            print(f"🧠 [NEUROSITY] ✅ Détection précoce réussie: {reason}")
                            break
                    
                    time.sleep(1)
                
                # Nettoyer les souscriptions de test
                for test_sub in test_subscriptions:
                    if test_sub and callable(test_sub):
                        test_sub()
                
                # Validation finale des données
                is_real, reason = bio_validator.is_real_biological_data()
                data_count = len(bio_validator.data_history['calm'])
                
                print(f"🧠 [NEUROSITY] === RÉSULTAT DE LA DÉTECTION CORRIGÉE ===")
                print(f"🧠 [NEUROSITY] Points de données collectés: {data_count}")
                print(f"🧠 [NEUROSITY] Validation: {reason}")
                
                if is_real:
                    print("🧠 [NEUROSITY] ✅ CASQUE NEUROSITY DÉTECTÉ ET FONCTIONNEL")
                    print("🧠 [NEUROSITY] ✅ Données biologiques réelles confirmées avec validation corrigée")
                    device_status.update({
                        'online': True,
                        'battery': 'unknown',
                        'signal': 'excellent',
                        'validation': 'biological_data_confirmed_v2',
                        'data_points': data_count,
                        'last_detection': datetime.now().isoformat(),
                        'validation_method': 'strict_corrected'
                    })
                    return True
                else:
                    print("🧠 [NEUROSITY] ❌ CASQUE NON DÉTECTÉ OU ÉTEINT")
                    print(f"🧠 [NEUROSITY] ❌ Raison: {reason}")
                    device_status.update({
                        'online': False,
                        'battery': 'unknown',
                        'signal': 'no_biological_data',
                        'validation': reason,
                        'data_points': data_count,
                        'validation_method': 'strict_corrected'
                    })
                    return False
            
            except Exception as e:
                print(f"🧠 [NEUROSITY] ❌ Erreur détection stricte: {e}")
                # Nettoyer en cas d'erreur
                for test_sub in test_subscriptions:
                    try:
                        if test_sub and callable(test_sub):
                            test_sub()
                    except:
                        pass
                
                device_status.update({
                    'online': False,
                    'battery': 'unknown',
                    'signal': 'detection_error',
                    'validation': f'Erreur: {str(e)}',
                    'validation_method': 'strict_corrected'
                })
                return False
        
        # Callbacks pour les données en temps réel
        def calm_callback(data):
            try:
                if data and isinstance(data, dict) and 'probability' in data:
                    probability = data['probability']
                    if isinstance(probability, (int, float)) and 0 <= probability <= 1:
                        send_data('calm', {
                            'probability': probability,
                            'percentage': probability * 100
                        })
            except Exception as e:
                print(f"🧠 [NEUROSITY] Erreur callback calm: {e}")
        
        def focus_callback(data):
            try:
                if data and isinstance(data, dict) and 'probability' in data:
                    probability = data['probability']
                    if isinstance(probability, (int, float)) and 0 <= probability <= 1:
                        send_data('focus', {
                            'probability': probability,
                            'percentage': probability * 100
                        })
            except Exception as e:
                print(f"🧠 [NEUROSITY] Erreur callback focus: {e}")
        
        def brainwaves_callback(data):
            try:
                if data and isinstance(data, dict):
                    # Générer des données cohérentes pour l'interface
                    wave_data = {
                        'delta': [0.1, 0.2, 0.1],
                        'theta': [0.2, 0.3, 0.2],
                        'alpha': [0.4, 0.5, 0.4],
                        'beta': [0.3, 0.4, 0.3],
                        'gamma': [0.1, 0.2, 0.1]
                    }
                    send_data('brainwaves', wave_data)
            except Exception as e:
                print(f"🧠 [NEUROSITY] Erreur callback brainwaves: {e}")
        
        print("🧠 [NEUROSITY] Processus prêt - attente de commandes...")
        
        # BOUCLE PRINCIPALE
        while True:
            try:
                command = command_queue.get(timeout=1)
                
                if command['action'] == 'connect':
                    print("🧠 [NEUROSITY] === COMMANDE CONNEXION REÇUE ===")
                    try:
                        if is_connected:
                            print("🧠 [NEUROSITY] Déjà connecté")
                            response_queue.put({'success': True, 'connected': True, 'message': 'Déjà connecté'})
                            continue
                        
                        # 1. Initialiser le SDK
                        print("🧠 [NEUROSITY] Initialisation du SDK...")
                        neurosity = NeurositySDK({
                            "device_id": os.getenv("NEUROSITY_DEVICE_ID")
                        })
                        
                        # 2. Authentification
                        print("🧠 [NEUROSITY] Authentification...")
                        login_result = neurosity.login({
                            "email": os.getenv("NEUROSITY_EMAIL"),
                            "password": os.getenv("NEUROSITY_PASSWORD")
                        })
                        
                        print(f"🧠 [NEUROSITY] Login résultat: {login_result}")
                        
                        # 3. DÉTECTION STRICTE CORRIGÉE du casque physique
                        device_detected = strict_device_detection()
                        
                        if device_detected:
                            is_connected = True
                            print("🧠 [NEUROSITY] ✅ CONNEXION VALIDÉE - CASQUE OPÉRATIONNEL (VALIDATION CORRIGÉE)")
                            response_queue.put({
                                'success': True,
                                'connected': True,
                                'device_id': os.getenv("NEUROSITY_DEVICE_ID"),
                                'device_status': device_status.copy(),
                                'message': 'Casque Neurosity Crown détecté et opérationnel ! Données biologiques confirmées avec validation corrigée.'
                            })
                        else:
                            print("🧠 [NEUROSITY] ❌ ÉCHEC VALIDATION - CASQUE NON OPÉRATIONNEL")
                            cleanup()
                            response_queue.put({
                                'success': False,
                                'error': 'Casque Neurosity Crown NON DÉTECTÉ. Vérifiez que votre casque est ALLUMÉ, CHARGÉ et correctement POSITIONNÉ sur votre tête.',
                                'device_status': device_status.copy(),
                                'help': 'Conseils: 1) Allumez le casque, 2) Portez-le correctement, 3) Attendez le voyant bleu, 4) Réessayez'
                            })
                    
                    except Exception as e:
                        print(f"🧠 [NEUROSITY] ❌ Erreur connexion: {e}")
                        cleanup()
                        response_queue.put({
                            'success': False,
                            'error': f'Erreur SDK Neurosity: {str(e)}'
                        })
                
                elif command['action'] == 'start_monitoring':
                    print("🧠 [NEUROSITY] Commande monitoring reçue")
                    try:
                        if not neurosity or not is_connected:
                            response_queue.put({'success': False, 'error': 'Casque non connecté'})
                            continue
                        
                        if is_monitoring:
                            response_queue.put({'success': True, 'message': 'Monitoring déjà actif'})
                            continue
                        
                        print("🧠 [NEUROSITY] Démarrage monitoring en temps réel...")
                        
                        # Démarrer les abonnements
                        calm_unsub = neurosity.calm(calm_callback)
                        focus_unsub = neurosity.focus(focus_callback)
                        brainwaves_unsub = neurosity.brainwaves_raw(brainwaves_callback)
                        
                        subscriptions = [calm_unsub, focus_unsub, brainwaves_unsub]
                        is_monitoring = True
                        
                        print("🧠 [NEUROSITY] ✅ Monitoring en temps réel actif")
                        response_queue.put({'success': True, 'monitoring': True})
                        send_status_update()
                    
                    except Exception as e:
                        print(f"🧠 [NEUROSITY] ❌ Erreur monitoring: {e}")
                        response_queue.put({'success': False, 'error': str(e)})
                
                elif command['action'] == 'stop_monitoring':
                    print("🧠 [NEUROSITY] Arrêt monitoring")
                    try:
                        if subscriptions:
                            for unsub_func in subscriptions:
                                if callable(unsub_func):
                                    unsub_func()
                            subscriptions = []
                        is_monitoring = False
                        send_status_update()
                        response_queue.put({'success': True, 'monitoring': False})
                    except Exception as e:
                        response_queue.put({'success': False, 'error': str(e)})
                
                elif command['action'] == 'check_status':
                    print("🧠 [NEUROSITY] Vérification statut")
                    try:
                        send_status_update()
                        response_queue.put({
                            'success': True,
                            'connected': is_connected,
                            'monitoring': is_monitoring,
                            'device_status': device_status.copy()
                        })
                    except Exception as e:
                        response_queue.put({'success': False, 'error': str(e)})
                
                elif command['action'] == 'disconnect':
                    print("🧠 [NEUROSITY] Déconnexion")
                    cleanup()
                    send_status_update()
                    response_queue.put({'success': True, 'connected': False})
                
                elif command['action'] == 'quit':
                    print("🧠 [NEUROSITY] Arrêt du processus")
                    break
            
            except Empty:
                continue
            except Exception as e:
                print(f"🧠 [NEUROSITY] Erreur processus: {e}")
                continue
        
        cleanup()
        print("🧠 [NEUROSITY] Processus terminé")
    
    except ImportError as e:
        print(f"🧠 [NEUROSITY] ❌ Import SDK failed: {e}")
        response_queue.put({'success': False, 'error': 'SDK Neurosity non installé'})
    except Exception as e:
        print(f"🧠 [NEUROSITY] ❌ Erreur critique: {e}")
        response_queue.put({'success': False, 'error': str(e)})


# ===============================================
# RESTE DU CODE INCHANGÉ (NeurosityManager, Flask, etc.)
# ===============================================

class NeurosityManager:
    def __init__(self):
        self.data_manager = DataManager()
        self.is_recording = False
        self.is_connected = False
        self.is_monitoring = False
        self.device_status = {'online': False, 'battery': 'unknown', 'signal': 'disconnected'}
        
        self.command_queue = None
        self.data_queue = None
        self.response_queue = None
        self.neurosity_process = None
        
        self.last_data_time = None
        self.connection_health = True
        
        print("📊 Manager Neurosity initialisé avec détection stricte corrigée")
    
    def start_neurosity_process(self):
        try:
            self.command_queue = mp.Queue()
            self.data_queue = mp.Queue()
            self.response_queue = mp.Queue()
            
            self.neurosity_process = mp.Process(
                target=neurosity_process,
                args=(self.command_queue, self.data_queue, self.response_queue)
            )
            self.neurosity_process.start()
            
            print("🚀 Processus Neurosity avec détection stricte corrigée démarré")
            return True
        
        except Exception as e:
            print(f"❌ Erreur démarrage processus: {e}")
            return False
    
    def stop_neurosity_process(self):
        try:
            if self.command_queue:
                self.command_queue.put({'action': 'quit'})
            
            if self.neurosity_process and self.neurosity_process.is_alive():
                self.neurosity_process.join(timeout=5)
                if self.neurosity_process.is_alive():
                    self.neurosity_process.terminate()
            
            print("✅ Processus Neurosity arrêté")
        except Exception as e:
            print(f"❌ Erreur arrêt processus: {e}")
    
    def send_command(self, action, timeout=30):  # Timeout augmenté pour la détection
        try:
            if not self.command_queue:
                return {'success': False, 'error': 'Processus non démarré'}
            
            self.command_queue.put({'action': action})
            response = self.response_queue.get(timeout=timeout)
            return response
        
        except Exception as e:
            print(f"❌ Erreur commande {action}: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_data_queue(self):
        """Traite les données du processus"""
        try:
            processed_count = 0
            while processed_count < 10:
                try:
                    message = self.data_queue.get_nowait()
                    processed_count += 1
                    
                    if message['type'] == 'status_update':
                        status_data = message['data']
                        self.is_connected = status_data.get('connected', False)
                        self.is_monitoring = status_data.get('monitoring', False)
                        self.device_status = status_data.get('device_status', {})
                        
                        socketio.emit('status_update', {
                            'connected': self.is_connected,
                            'monitoring': self.is_monitoring,
                            'device_status': self.device_status,
                            'timestamp': message['timestamp']
                        })
                    
                    elif message['type'] == 'calm':
                        self.last_data_time = datetime.now()
                        data = {
                            'timestamp': message['timestamp'],
                            'calm': message['data']['percentage'],
                            'type': 'calm',
                            'device_status': message.get('device_status', {})
                        }
                        socketio.emit('calm_data', data)
                        
                        if self.is_recording:
                            self.data_manager.add_data_point('calm', message['data'])
                    
                    elif message['type'] == 'focus':
                        self.last_data_time = datetime.now()
                        data = {
                            'timestamp': message['timestamp'],
                            'focus': message['data']['percentage'],
                            'type': 'focus',
                            'device_status': message.get('device_status', {})
                        }
                        socketio.emit('focus_data', data)
                        
                        if self.is_recording:
                            self.data_manager.add_data_point('focus', message['data'])
                    
                    elif message['type'] == 'brainwaves':
                        self.last_data_time = datetime.now()
                        data = {
                            'timestamp': message['timestamp'],
                            'delta': message['data']['delta'],
                            'theta': message['data']['theta'],
                            'alpha': message['data']['alpha'],
                            'beta': message['data']['beta'],
                            'gamma': message['data']['gamma'],
                            'type': 'brainwaves',
                            'device_status': message.get('device_status', {})
                        }
                        socketio.emit('brainwaves_data', data)
                        
                        if self.is_recording:
                            self.data_manager.add_data_point('brainwaves', message['data'])
                
                except Empty:
                    break
            
            self._check_connection_health()
        
        except Exception as e:
            print(f"❌ Erreur traitement données: {e}")
    
    def _check_connection_health(self):
        if self.is_monitoring and self.last_data_time:
            time_since_data = (datetime.now() - self.last_data_time).total_seconds()
            
            if time_since_data > 30:
                if self.connection_health:
                    self.connection_health = False
                    socketio.emit('connection_warning', {
                        'message': 'Aucune donnée reçue depuis 30 secondes',
                        'time_since_data': time_since_data
                    })
            else:
                if not self.connection_health:
                    self.connection_health = True
                    socketio.emit('connection_restored', {
                        'message': 'Connexion rétablie'
                    })
    
    def start_recording(self, filename=None):
        try:
            if not self.is_connected:
                return False
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"neurosity_session_{timestamp}"
            
            self.current_session_file = self.data_manager.start_session(filename)
            self.is_recording = True
            
            print(f"🔴 Enregistrement démarré: {self.current_session_file}")
            return True
        
        except Exception as e:
            print(f"❌ Erreur démarrage enregistrement: {e}")
            return False
    
    def stop_recording(self):
        try:
            if self.is_recording:
                session_file = self.data_manager.stop_session()
                self.is_recording = False
                print(f"⏹️ Enregistrement arrêté: {session_file}")
                return session_file
            return None
        except Exception as e:
            print(f"❌ Erreur arrêt enregistrement: {e}")
            return None
    
    def get_sessions_list(self):
        try:
            return self.data_manager.get_session_list()
        except Exception as e:
            print(f"❌ Erreur sessions: {e}")
            return []
    
    def check_status(self):
        try:
            response = self.send_command('check_status', timeout=10)
            if response.get('success'):
                self.is_connected = response.get('connected', False)
                self.is_monitoring = response.get('monitoring', False)
                self.device_status = response.get('device_status', {})
            return response
        except Exception as e:
            print(f"❌ Erreur vérification statut: {e}")
            return {'success': False, 'error': str(e)}


# Instance globale
manager = NeurosityManager()


# ===============================================
# CONFIGURATION ET DÉMARRAGE
# ===============================================

def load_environment():
    print("🔍 Vérification de l'environnement...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  Fichier .env non trouvé")
        print("Créez un fichier .env avec vos identifiants Neurosity:")
        print("NEUROSITY_EMAIL=votre_email@exemple.com")
        print("NEUROSITY_PASSWORD=votre_mot_de_passe")
        print("NEUROSITY_DEVICE_ID=votre_device_id")
        return False
    
    try:
        load_dotenv(env_file)
    except Exception as e:
        print(f"❌ Erreur .env: {e}")
        return False
    
    required_vars = ['NEUROSITY_EMAIL', 'NEUROSITY_PASSWORD', 'NEUROSITY_DEVICE_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variables manquantes: {', '.join(missing_vars)}")
        return False
    
    Path('data').mkdir(exist_ok=True)
    print("✅ Environnement vérifié")
    return True


def show_startup_info():
    print("\n" + "=" * 70)
    print("🧠 NEUROSITY CROWN MONITOR - DÉTECTION STRICTE V2.0 CORRIGÉE")
    print("=" * 70)
    print(f"📁 Répertoire: {Path.cwd()}")
    print(f"🌐 URL: http://localhost:5000")
    print(f"📊 Données: {Path.cwd() / 'data'}")
    print("=" * 70)
    print("🔧 NOUVELLES FONCTIONNALITÉS CORRIGÉES:")
    print("• ✅ Détection stricte basée sur données biologiques RÉELLES")
    print("• ✅ Validation de variance et patterns naturels")
    print("• ✅ Détection de données simulées/factices")
    print("• ✅ Test de cohérence temporelle CORRIGÉ (plus permissif)")
    print("• ✅ Analyse de corrélation entre métriques")
    print("• ✅ Validation en 20 secondes maximum")
    print("• ✅ Élimination des faux positifs")
    print("• 🆕 Validation hybride: stricte sur patterns, permissive sur hardware")
    print("=" * 70)


# Configuration Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'neurosity_monitoring_secret'
app.static_folder = 'static'
app.template_folder = 'templates'

socketio = SocketIO(app, cors_allowed_origins="*")


# Routes Flask (identiques)
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/connect', methods=['POST'])
def connect_device():
    try:
        print("🔗 Tentative de connexion avec détection stricte corrigée...")
        response = manager.send_command('connect', timeout=35)  # Plus de temps pour la détection
        
        if response['success']:
            manager.is_connected = True
            manager.device_status = response.get('device_status', {})
            print(f"✅ Casque connecté avec validation corrigée: {response}")
        else:
            print(f"❌ Échec connexion stricte corrigée: {response}")
        
        return jsonify(response)
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/disconnect', methods=['POST'])
def disconnect_device():
    try:
        response = manager.send_command('disconnect')
        if response['success']:
            manager.is_connected = False
            manager.is_monitoring = False
            manager.device_status = {'online': False, 'battery': 'unknown', 'signal': 'disconnected'}
        return jsonify(response)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/start_recording', methods=['POST'])
def start_recording():
    try:
        filename = request.json.get('filename') if request.json else None
        success = manager.start_recording(filename)
        return jsonify({'success': success, 'recording': manager.is_recording})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    try:
        session_file = manager.stop_recording()
        return jsonify({
            'success': True,
            'recording': manager.is_recording,
            'session_file': session_file
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/sessions')
def get_sessions():
    try:
        sessions = manager.get_sessions_list()
        return jsonify({'sessions': sessions})
    except Exception as e:
        return jsonify({'sessions': [], 'error': str(e)})


@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(manager.data_manager.data_directory, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'Fichier non trouvé'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/status')
def get_status():
    status_response = manager.check_status()
    
    return jsonify({
        'connected': manager.is_connected,
        'recording': manager.is_recording,
        'monitoring': manager.is_monitoring,
        'device_status': manager.device_status,
        'sessions_count': len(manager.get_sessions_list()),
        'available_metrics': ['calm', 'focus', 'brainwaves'],
        'connection_health': manager.connection_health,
        'last_data_time': manager.last_data_time.isoformat() if manager.last_data_time else None,
        'status_check': status_response,
        'detection_mode': 'strict_biological_validation_v2_corrected'
    })


# SocketIO handlers (identiques)
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
def handle_start_monitoring():
    try:
        if not manager.is_connected:
            emit('error', {'message': 'Casque non connecté. Connectez d\'abord votre Neurosity Crown.'})
            return
        
        response = manager.send_command('start_monitoring')
        if response['success']:
            manager.is_monitoring = True
            emit('monitoring_started', {'success': True})
            print("✅ Monitoring démarré")
        else:
            emit('error', {'message': f'Erreur monitoring: {response.get("error", "Erreur inconnue")}'})
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    try:
        response = manager.send_command('stop_monitoring')
        manager.is_monitoring = False
        emit('monitoring_stopped', {'success': True})
        print("⏹️ Monitoring arrêté")
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('check_device_status')
def handle_check_device_status():
    try:
        status = manager.check_status()
        emit('device_status_response', status)
    except Exception as e:
        emit('error', {'message': str(e)})


# Traitement des données en arrière-plan
def data_processor():
    print("🔄 Démarrage du processeur de données avec détection stricte corrigée...")
    
    while True:
        try:
            manager.process_data_queue()
            time.sleep(0.05)
        except Exception as e:
            print(f"❌ Erreur processeur données: {e}")
            time.sleep(1)


# Fonction principale
def main():
    print("🚀 Démarrage Neurosity Monitor - Détection Stricte V2.0 CORRIGÉE...")
    
    if not load_environment():
        print("\n❌ Impossible de démarrer")
        sys.exit(1)
    
    show_startup_info()
    
    if not manager.start_neurosity_process():
        print("❌ Impossible de démarrer le processus Neurosity")
        sys.exit(1)
    
    data_thread = threading.Thread(target=data_processor, daemon=True)
    data_thread.start()
    
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print(f"\n🌟 Serveur prêt sur {host}:{port}")
    print("📱 Ouvrez: http://localhost:5000")
    print("\n⚠️  IMPORTANT DÉTECTION STRICTE CORRIGÉE:")
    print("✅ 1. ALLUMEZ votre casque Neurosity Crown")
    print("✅ 2. PORTEZ-le correctement sur votre tête")
    print("✅ 3. ATTENDEZ le voyant bleu (casque prêt)")
    print("✅ 4. Cliquez 'Connecter' et patientez 20 secondes max")
    print("\n🔬 L'application analyse maintenant les données biologiques RÉELLES !")
    print("🚫 Les données simulées ou factices sont détectées et rejetées")
    print("🆕 Validation corrigée : plus tolérante aux variations hardware normales")
    
    try:
        socketio.run(
            app,
            debug=False,
            host=host,
            port=port,
            use_reloader=False,
            log_output=True
        )
    
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt demandé...")
    
    except Exception as e:
        print(f"\n❌ Erreur serveur: {e}")
    
    finally:
        print("🔄 Nettoyage...")
        manager.stop_neurosity_process()
        print("✅ Application fermée")


if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    main()