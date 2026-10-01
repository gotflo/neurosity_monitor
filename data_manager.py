#!/usr/bin/env python3
"""
DataManager optimisé pour Neurosity Monitor
Gestion des données CSV avec EEG brut et système de buffer
Version avec 8 valeurs par bande d'ondes cérébrales
"""

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import statistics
import json
import logging

logger = logging.getLogger(__name__)


class DataManager:
    """Gestionnaire de données pour les sessions Neurosity"""
    
    # Headers CSV mis à jour pour inclure les 8 valeurs de chaque bande
    CSV_HEADERS = [
        'timestamp', 'session_duration',
        'calm_probability', 'focus_probability',
        # Delta (8 électrodes)
        'delta_CP3', 'delta_C3', 'delta_F5', 'delta_PO3',
        'delta_PO4', 'delta_F6', 'delta_C4', 'delta_CP4',
        # Theta (8 électrodes)
        'theta_CP3', 'theta_C3', 'theta_F5', 'theta_PO3',
        'theta_PO4', 'theta_F6', 'theta_C4', 'theta_CP4',
        # Alpha (8 électrodes)
        'alpha_CP3', 'alpha_C3', 'alpha_F5', 'alpha_PO3',
        'alpha_PO4', 'alpha_F6', 'alpha_C4', 'alpha_CP4',
        # Beta (8 électrodes)
        'beta_CP3', 'beta_C3', 'beta_F5', 'beta_PO3',
        'beta_PO4', 'beta_F6', 'beta_C4', 'beta_CP4',
        # Gamma (8 électrodes)
        'gamma_CP3', 'gamma_C3', 'gamma_F5', 'gamma_PO3',
        'gamma_PO4', 'gamma_F6', 'gamma_C4', 'gamma_CP4',
        # EEG brut (8 électrodes)
        'eeg_CP3', 'eeg_C3', 'eeg_F5', 'eeg_PO3',
        'eeg_PO4', 'eeg_F6', 'eeg_C4', 'eeg_CP4',
        # Qualité du signal - statut (8 électrodes)
        'signal_status_CP3', 'signal_status_C3', 'signal_status_F5', 'signal_status_PO3',
        'signal_status_PO4', 'signal_status_F6', 'signal_status_C4', 'signal_status_CP4',
        # Qualité du signal - écart-type (8 électrodes)
        'signal_std_CP3', 'signal_std_C3', 'signal_std_F5', 'signal_std_PO3',
        'signal_std_PO4', 'signal_std_F6', 'signal_std_C4', 'signal_std_CP4'
    ]

    # Noms des électrodes dans l'ordre
    ELECTRODE_NAMES = ['CP3', 'C3', 'F5', 'PO3', 'PO4', 'F6', 'C4', 'CP4']

    # Statuts de qualité du signal renvoyés par le SDK Neurosity
    SIGNAL_QUALITY_STATUSES = ['great', 'good', 'bad', 'noContact']
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)
        self.current_session = None
        self.csv_file = None
        self.csv_writer = None
        self.session_start_time = None
        
        # Buffer pour stocker temporairement les dernières valeurs
        self.data_buffer = {
            'calm_probability': None,
            'focus_probability': None,
            'brainwaves': {},  # Stockera les 8 valeurs pour chaque bande
            'eeg_raw': {},
            'signal_quality': {}  # Dernier statut/ecart-type connu par electrode
        }
        
        # Créer le dossier de données
        self.data_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"DataManager initialisé - Dossier: {self.data_directory}")
        
        # Statistiques
        self.write_interval = 0  # Compteur pour écrire périodiquement
    
    def start_session(self, session_name: Optional[str] = None) -> str:
        """Démarre une nouvelle session d'enregistrement"""
        # Fermer la session précédente si elle existe
        if self.csv_file and not self.csv_file.closed:
            self.stop_session()
        
        # Générer le nom de session
        if not session_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"neurosity_session_{timestamp}"
        
        self.current_session = session_name
        csv_filename = self.data_directory / f"{session_name}.csv"
        
        try:
            # Ouvrir le fichier CSV avec encodage UTF-8
            self.csv_file = open(csv_filename, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.DictWriter(
                self.csv_file,
                fieldnames=self.CSV_HEADERS,
                delimiter=';'
            )
            self.csv_writer.writeheader()
            
            self.session_start_time = datetime.now()
            
            # Réinitialiser le buffer
            self.data_buffer = {
                'calm_probability': None,
                'focus_probability': None,
                'brainwaves': {},
                'eeg_raw': {},
                'signal_quality': {}
            }
            
            logger.info(f"Session démarrée: {csv_filename}")
            return str(csv_filename)
        
        except Exception as e:
            logger.error(f"Erreur démarrage session: {e}")
            self._cleanup()
            raise
    
    def add_data_point(self, data_type: str, data: Dict, metadata: Optional[Dict] = None):
        """Ajoute un point de données au buffer ou écrit une ligne complète"""
        if not self.current_session or not self.csv_writer:
            return
        
        try:
            # Mettre à jour le buffer selon le type de données
            if data_type == 'calm':
                self.data_buffer['calm_probability'] = data.get('probability', 0)
            
            elif data_type == 'focus':
                self.data_buffer['focus_probability'] = data.get('probability', 0)
            
            elif data_type == 'brainwaves':
                # Stocker toutes les 8 valeurs pour chaque bande
                for wave in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                    if wave in data and isinstance(data[wave], list) and len(data[wave]) == 8:
                        self.data_buffer['brainwaves'][wave] = data[wave]
                        logger.debug(f"Brainwave {wave}: {len(data[wave])} valeurs enregistrées")
            
            elif data_type == 'brainwaves_raw':
                # Traiter les données EEG brutes
                if 'data' in data and isinstance(data['data'], list) and len(data['data']) == 8:
                    raw_data = data['data']
                    
                    # Calculer la moyenne pour chaque canal (pour réduire la quantité de données)
                    for i, channel in enumerate(self.ELECTRODE_NAMES):
                        if i < len(raw_data) and isinstance(raw_data[i], list) and raw_data[i]:
                            # Prendre la moyenne des échantillons pour ce canal
                            avg_value = sum(raw_data[i]) / len(raw_data[i])
                            self.data_buffer['eeg_raw'][f'eeg_{channel}'] = round(avg_value, 3)

            elif data_type == 'signal_quality':
                # SDK Neurosity : { <electrode>: {status, standardDeviation} }
                # Statuts possibles : great | good | bad | noContact
                for electrode in self.ELECTRODE_NAMES:
                    quality = data.get(electrode)
                    if not isinstance(quality, dict):
                        continue

                    status = quality.get('status', 'noContact')
                    if status not in self.SIGNAL_QUALITY_STATUSES:
                        logger.debug(f"Statut de signal inconnu pour {electrode}: {status}")

                    std_dev = quality.get('standardDeviation', 0)
                    self.data_buffer['signal_quality'][electrode] = {
                        'status': status,
                        'standardDeviation': round(std_dev, 3) if isinstance(std_dev, (int, float)) else 0
                    }

                # La qualité du signal est une métadonnée d'acquisition : elle
                # met à jour le buffer mais ne déclenche pas d'écriture, sinon
                # elle ajouterait des lignes qui dupliquent les échantillons EEG
                # précédents. Elle est jointe à la prochaine ligne produite par
                # les flux calm / focus / brainwaves / EEG brut.
                return

            # Écrire une ligne si nous avons suffisamment de données
            self._write_row_if_ready()
        
        except Exception as e:
            logger.error(f"Erreur ajout données: {e}")
    
    def _write_row_if_ready(self):
        """Écrit une ligne dans le CSV si nous avons des données suffisantes"""
        # Vérifier si nous avons au moins quelques données de base
        if (self.data_buffer['calm_probability'] is not None or
                self.data_buffer['focus_probability'] is not None or
                self.data_buffer['brainwaves'] or
                self.data_buffer['eeg_raw']):
            
            timestamp = datetime.now()
            session_duration = (timestamp - self.session_start_time).total_seconds() if self.session_start_time else 0
            
            # Construire la ligne de données
            row_data = {
                'timestamp': timestamp.isoformat(),
                'session_duration': round(session_duration, 2),
                'calm_probability': self.data_buffer['calm_probability'] or '',
                'focus_probability': self.data_buffer['focus_probability'] or ''
            }
            
            # Ajouter les ondes cérébrales (8 valeurs par bande)
            for wave in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                if wave in self.data_buffer['brainwaves'] and isinstance(self.data_buffer['brainwaves'][wave], list):
                    values = self.data_buffer['brainwaves'][wave]
                    for i, electrode in enumerate(self.ELECTRODE_NAMES):
                        key = f'{wave}_{electrode}'
                        if i < len(values):
                            row_data[key] = round(values[i], 3)
                        else:
                            row_data[key] = ''
                else:
                    # Si pas de données, laisser vide
                    for electrode in self.ELECTRODE_NAMES:
                        row_data[f'{wave}_{electrode}'] = ''
            
            # Ajouter les données EEG brutes
            for electrode in self.ELECTRODE_NAMES:
                key = f'eeg_{electrode}'
                row_data[key] = self.data_buffer['eeg_raw'].get(key, '')

            # Ajouter la qualité du signal (dernier état connu par électrode)
            for electrode in self.ELECTRODE_NAMES:
                quality = self.data_buffer['signal_quality'].get(electrode)
                row_data[f'signal_status_{electrode}'] = quality['status'] if quality else ''
                row_data[f'signal_std_{electrode}'] = quality['standardDeviation'] if quality else ''
            
            # Écrire la ligne
            self.csv_writer.writerow(row_data)
            self.csv_file.flush()
            
            # Optionnel : réinitialiser certaines parties du buffer après écriture
            # self.data_buffer['eeg_raw'] = {}  # Décommenter si vous voulez réinitialiser après chaque écriture
    
    def stop_session(self) -> Optional[str]:
        """Arrête la session d'enregistrement en cours"""
        if not self.csv_file:
            return None
        
        csv_path = self.csv_file.name
        
        try:
            self.csv_file.close()
            logger.info(f"Session terminée: {csv_path}")
        except Exception as e:
            logger.error(f"Erreur arrêt session: {e}")
        finally:
            self._cleanup()
        
        return csv_path
    
    def get_session_list(self) -> List[str]:
        """Retourne la liste des sessions disponibles"""
        try:
            csv_files = [
                f.name for f in self.data_directory.glob("*.csv")
                if f.is_file()
            ]
            return sorted(csv_files, reverse=True)
        except Exception as e:
            logger.error(f"Erreur liste sessions: {e}")
            return []
    
    def analyze_session(self, csv_filename: str) -> Dict[str, Any]:
        """Analyse basique d'une session"""
        csv_path = self.data_directory / csv_filename
        
        if not csv_path.exists():
            return {'error': 'Fichier non trouvé'}
        
        try:
            analysis = {
                'filename': csv_filename,
                'total_points': 0,
                'duration': 0,
                'metrics': {},
                'brainwaves': {},
                'brainwaves_by_electrode': {},
                'eeg_channels': {},
                'signal_quality': {}
            }
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                rows = list(reader)
                
                if rows:
                    analysis['total_points'] = len(rows)
                    
                    # Durée de la session
                    if rows[-1].get('session_duration'):
                        analysis['duration'] = float(rows[-1]['session_duration'])
                    
                    # Statistiques des métriques
                    for metric in ['calm_probability', 'focus_probability']:
                        values = [
                            float(row[metric])
                            for row in rows
                            if row.get(metric) and row[metric].strip()
                        ]
                        if values:
                            analysis['metrics'][metric] = {
                                'mean': round(statistics.mean(values), 1),
                                'min': round(min(values), 1),
                                'max': round(max(values), 1),
                                'stdev': round(statistics.stdev(values), 1) if len(values) > 1 else 0
                            }
                    
                    # Statistiques des ondes cérébrales (moyenne globale)
                    for wave in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                        all_values = []
                        electrode_stats = {}
                        
                        for electrode in self.ELECTRODE_NAMES:
                            key = f'{wave}_{electrode}'
                            values = [
                                float(row[key])
                                for row in rows
                                if row.get(key) and row[key].strip()
                            ]
                            if values:
                                all_values.extend(values)
                                electrode_stats[electrode] = {
                                    'mean': round(statistics.mean(values), 3),
                                    'min': round(min(values), 3),
                                    'max': round(max(values), 3)
                                }
                        
                        if all_values:
                            analysis['brainwaves'][wave] = {
                                'mean': round(statistics.mean(all_values), 3),
                                'min': round(min(all_values), 3),
                                'max': round(max(all_values), 3)
                            }
                            analysis['brainwaves_by_electrode'][wave] = electrode_stats
                    
                    # Statistiques EEG par canal
                    for electrode in self.ELECTRODE_NAMES:
                        key = f'eeg_{electrode}'
                        values = [
                            float(row[key])
                            for row in rows
                            if row.get(key) and row[key].strip()
                        ]
                        if values:
                            analysis['eeg_channels'][electrode] = {
                                'mean': round(statistics.mean(values), 3),
                                'std': round(statistics.stdev(values), 3) if len(values) > 1 else 0,
                                'min': round(min(values), 3),
                                'max': round(max(values), 3)
                            }

                    # Qualité du signal par électrode (répartition des statuts
                    # + statistiques d'écart-type). Absent des anciennes sessions.
                    for electrode in self.ELECTRODE_NAMES:
                        status_key = f'signal_status_{electrode}'
                        std_key = f'signal_std_{electrode}'

                        statuses = [
                            row[status_key]
                            for row in rows
                            if row.get(status_key) and row[status_key].strip()
                        ]
                        std_values = [
                            float(row[std_key])
                            for row in rows
                            if row.get(std_key) and row[std_key].strip()
                        ]

                        if not statuses and not std_values:
                            continue

                        distribution = {
                            status: statuses.count(status)
                            for status in self.SIGNAL_QUALITY_STATUSES
                            if statuses.count(status) > 0
                        }

                        electrode_quality = {
                            'samples': len(statuses),
                            'status_distribution': distribution
                        }

                        if statuses:
                            # Statut dominant et part du temps en contact exploitable
                            electrode_quality['dominant_status'] = max(distribution, key=distribution.get)
                            usable = distribution.get('great', 0) + distribution.get('good', 0)
                            electrode_quality['usable_percent'] = round(100 * usable / len(statuses), 1)

                        if std_values:
                            electrode_quality['standard_deviation'] = {
                                'mean': round(statistics.mean(std_values), 3),
                                'min': round(min(std_values), 3),
                                'max': round(max(std_values), 3)
                            }

                        analysis['signal_quality'][electrode] = electrode_quality

            return analysis
        
        except Exception as e:
            logger.error(f"Erreur analyse session: {e}")
            return {'error': str(e)}
    
    def cleanup_old_sessions(self, days_to_keep: int = 30):
        """Supprime les sessions anciennes"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for csv_file in self.data_directory.glob("*.csv"):
                try:
                    file_time = datetime.fromtimestamp(csv_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        csv_file.unlink()
                        deleted_count += 1
                        logger.info(f"Session supprimée: {csv_file.name}")
                except Exception as e:
                    logger.error(f"Erreur suppression {csv_file.name}: {e}")
            
            if deleted_count > 0:
                logger.info(f"{deleted_count} session(s) supprimée(s)")
        
        except Exception as e:
            logger.error(f"Erreur nettoyage: {e}")
    
    def export_session_to_json(self, csv_filename: str) -> Optional[Dict]:
        """Exporte une session en format JSON"""
        csv_path = self.data_directory / csv_filename
        
        if not csv_path.exists():
            return None
        
        try:
            data = {
                'filename': csv_filename,
                'exported_at': datetime.now().isoformat(),
                'electrodes': self.ELECTRODE_NAMES,
                'data_points': []
            }
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    # Convertir les valeurs numériques
                    point = {}
                    for key, value in row.items():
                        if value:
                            # Colonnes numériques
                            if key in ['session_duration', 'calm_probability', 'focus_probability'] or \
                                    any(key.startswith(prefix + '_') for prefix in
                                        ['delta', 'theta', 'alpha', 'beta', 'gamma', 'eeg']):
                                try:
                                    point[key] = float(value)
                                except:
                                    point[key] = value
                            else:
                                point[key] = value
                    
                    data['data_points'].append(point)
            
            return data
        
        except Exception as e:
            logger.error(f"Erreur export JSON: {e}")
            return None
    
    def _cleanup(self):
        """Nettoie les ressources"""
        if self.csv_file and not self.csv_file.closed:
            try:
                self.csv_file.close()
            except:
                pass
        
        self.csv_file = None
        self.csv_writer = None
        self.current_session = None
        self.session_start_time = None
        self.data_buffer = {
            'calm_probability': None,
            'focus_probability': None,
            'brainwaves': {},
            'eeg_raw': {},
            'signal_quality': {}
        }
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Retourne des informations sur l'espace de stockage"""
        try:
            total_size = 0
            file_count = 0
            
            for csv_file in self.data_directory.glob("*.csv"):
                if csv_file.is_file():
                    total_size += csv_file.stat().st_size
                    file_count += 1
            
            return {
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'directory': str(self.data_directory)
            }
        
        except Exception as e:
            logger.error(f"Erreur info stockage: {e}")
            return {'error': str(e)}