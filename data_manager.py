"""
DataManager optimisé pour Neurosity Monitor
Gestion simplifiée des données CSV
"""

import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics

class DataManager:
    """Gestionnaire de données pour les sessions Neurosity"""
    
    CSV_HEADERS = [
        'timestamp', 'session_duration',
        'calm_probability', 'calm_percentage',
        'focus_probability', 'focus_percentage',
        'delta', 'theta', 'alpha', 'beta', 'gamma'
    ]
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = data_directory
        self.current_session = None
        self.csv_file = None
        self.csv_writer = None
        self.session_start_time = None
        
        # Créer le dossier de données
        os.makedirs(data_directory, exist_ok=True)
    
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
        csv_filename = os.path.join(self.data_directory, f"{session_name}.csv")
        
        try:
            # Ouvrir le fichier CSV
            self.csv_file = open(csv_filename, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.DictWriter(
                self.csv_file,
                fieldnames=self.CSV_HEADERS,
                delimiter=';'
            )
            self.csv_writer.writeheader()
            
            self.session_start_time = datetime.now()
            
            print(f"Session démarrée: {csv_filename}")
            return csv_filename
        
        except Exception as e:
            print(f"Erreur démarrage session: {e}")
            self._cleanup()
            raise
    
    def add_data_point(self, data_type: str, data: Dict, metadata: Optional[Dict] = None):
        """Ajoute un point de données à la session courante"""
        if not self.current_session or not self.csv_writer:
            return
        
        try:
            # Créer la ligne de données
            timestamp = datetime.now()
            session_duration = (timestamp - self.session_start_time).total_seconds() if self.session_start_time else 0
            
            row_data = {
                'timestamp': timestamp.isoformat(),
                'session_duration': round(session_duration, 2)
            }
            
            # Ajouter les données selon le type
            if data_type == 'calm':
                probability = data.get('probability', 0)
                row_data.update({
                    'calm_probability': probability,
                    'calm_percentage': round(probability * 100, 1)
                })
            elif data_type == 'focus':
                probability = data.get('probability', 0)
                row_data.update({
                    'focus_probability': probability,
                    'focus_percentage': round(probability * 100, 1)
                })
            elif data_type == 'brainwaves':
                for wave in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                    row_data[wave] = round(data.get(wave, 0), 3)
            
            # Écrire la ligne
            complete_row = {col: row_data.get(col, '') for col in self.CSV_HEADERS}
            self.csv_writer.writerow(complete_row)
            self.csv_file.flush()
        
        except Exception as e:
            print(f"Erreur ajout données: {e}")
    
    def stop_session(self) -> Optional[str]:
        """Arrête la session d'enregistrement en cours"""
        if not self.csv_file:
            return None
        
        csv_path = self.csv_file.name
        
        try:
            self.csv_file.close()
            print(f"Session terminée: {csv_path}")
        except Exception as e:
            print(f"Erreur arrêt session: {e}")
        finally:
            self._cleanup()
        
        return csv_path
    
    def get_session_list(self) -> List[str]:
        """Retourne la liste des sessions disponibles"""
        try:
            csv_files = [
                f for f in os.listdir(self.data_directory)
                if f.endswith('.csv') and os.path.isfile(os.path.join(self.data_directory, f))
            ]
            return sorted(csv_files, reverse=True)
        except Exception as e:
            print(f"Erreur liste sessions: {e}")
            return []
    
    def analyze_session(self, csv_filename: str) -> Dict[str, Any]:
        """Analyse basique d'une session"""
        csv_path = os.path.join(self.data_directory, csv_filename)
        
        if not os.path.exists(csv_path):
            return {'error': 'Fichier non trouvé'}
        
        try:
            analysis = {
                'filename': csv_filename,
                'total_points': 0,
                'duration': 0,
                'metrics': {}
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
                    for metric in ['calm_percentage', 'focus_percentage']:
                        values = [
                            float(row[metric])
                            for row in rows
                            if row.get(metric) and row[metric].strip()
                        ]
                        if values:
                            analysis['metrics'][metric] = {
                                'mean': statistics.mean(values),
                                'min': min(values),
                                'max': max(values)
                            }
            
            return analysis
        
        except Exception as e:
            print(f"Erreur analyse session: {e}")
            return {'error': str(e)}
    
    def cleanup_old_sessions(self, days_to_keep: int = 30):
        """Supprime les sessions anciennes"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            sessions = self.get_session_list()
            deleted_count = 0
            
            for session in sessions:
                session_path = os.path.join(self.data_directory, session)
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(session_path))
                    if file_time < cutoff_date:
                        os.remove(session_path)
                        deleted_count += 1
                except Exception as e:
                    print(f"Erreur suppression {session}: {e}")
            
            if deleted_count > 0:
                print(f"{deleted_count} session(s) supprimée(s)")
        
        except Exception as e:
            print(f"Erreur nettoyage: {e}")
    
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
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Retourne des informations sur l'espace de stockage"""
        try:
            total_size = 0
            file_count = 0
            
            for filename in os.listdir(self.data_directory):
                file_path = os.path.join(self.data_directory, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
                    if filename.endswith('.csv'):
                        file_count += 1
            
            return {
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'directory': self.data_directory
            }
        except Exception as e:
            print(f"Erreur info stockage: {e}")
            return {'error': str(e)}