import csv
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd


class DataManager:
    """Gestionnaire avancé pour les données Neurosity avec export CSV optimisé"""
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = data_directory
        self.current_session = None
        self.csv_file = None
        self.csv_writer = None
        self.session_data = []
        self.session_start_time = None
        
        # Créer le dossier de données s'il n'existe pas
        os.makedirs(data_directory, exist_ok=True)
    
    def start_session(self, session_name: Optional[str] = None) -> str:
        """Démarre une nouvelle session d'enregistrement"""
        if not session_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"neurosity_session_{timestamp}"
        
        self.current_session = session_name
        csv_filename = os.path.join(self.data_directory, f"{session_name}.csv")
        
        # CORRECTION: Fermer le fichier précédent s'il existe
        if self.csv_file and not self.csv_file.closed:
            self.csv_file.close()
        
        # Ouvrir le fichier CSV avec le bon délimiteur
        self.csv_file = open(csv_filename, 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file, delimiter=';')
        
        headers = [
            'timestamp',
            'session_duration',
            'calm_probability',
            'calm_percentage',
            'focus_probability',
            'focus_percentage',
            'attention_probability',
            'attention_percentage',
            'delta_avg',
            'delta_max',
            'delta_min',
            'delta_std',
            'delta_raw',
            'theta_avg',
            'theta_max',
            'theta_min',
            'theta_std',
            'theta_raw',
            'alpha_avg',
            'alpha_max',
            'alpha_min',
            'alpha_std',
            'alpha_raw',
            'beta_avg',
            'beta_max',
            'beta_min',
            'beta_std',
            'beta_raw',
            'gamma_avg',
            'gamma_max',
            'gamma_min',
            'gamma_std',
            'gamma_raw'
        ]
        
        self.csv_writer.writerow(headers)
        self.session_start_time = datetime.now()
        self.session_data = []
        
        print(f"Session d'enregistrement démarrée: {csv_filename}")
        return csv_filename
    
    def add_data_point(self, data_type: str, data: Dict, metadata: Optional[Dict] = None):
        """Ajoute un point de données à la session courante"""
        if not self.current_session or not self.csv_writer:
            print("Aucune session active. Démarrez une session d'abord.")
            return
        
        # CORRECTION: Vérifier que session_start_time existe
        if not self.session_start_time:
            self.session_start_time = datetime.now()
        
        timestamp = datetime.now()
        session_duration = (timestamp - self.session_start_time).total_seconds()
        
        # CORRECTION: Initialiser la ligne avec les données de base simplifiées
        row_data = {
            'timestamp': timestamp.isoformat(),
            'session_duration': session_duration,
            'device_id': metadata.get('device_id', '') if metadata else ''
        }
        
        # Traiter selon le type de données
        if data_type == 'calm':
            self._process_calm_data(row_data, data)
        elif data_type == 'focus':
            self._process_focus_data(row_data, data)
        elif data_type == 'attention':
            self._process_attention_data(row_data, data)
        elif data_type == 'brainwaves':
            self._process_brainwaves_data(row_data, data)
        
        # Stocker en mémoire pour analyse
        self.session_data.append(row_data.copy())
        
        # CORRECTION: Écrire dans le CSV immédiatement avec gestion d'erreurs
        try:
            self._write_csv_row(row_data)
        except Exception as e:
            print(f"Erreur écriture CSV: {e}")
    
    def _process_calm_data(self, row_data: Dict, data: Dict):
        """Traite les données de calme"""
        probability = data.get('probability', 0)
        row_data.update({
            'calm_probability': probability,
            'calm_percentage': probability * 100
        })
    
    def _process_focus_data(self, row_data: Dict, data: Dict):
        """Traite les données de concentration"""
        probability = data.get('probability', 0)
        row_data.update({
            'focus_probability': probability,
            'focus_percentage': probability * 100
        })
    
    def _process_attention_data(self, row_data: Dict, data: Dict):
        """Traite les données d'attention"""
        probability = data.get('probability', 0)
        row_data.update({
            'attention_probability': probability,
            'attention_percentage': probability * 100
        })
    
    def _process_brainwaves_data(self, row_data: Dict, data: Dict):
        """Traite les données des ondes cérébrales avec statistiques"""
        for wave_type in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
            wave_data = data.get(wave_type, [])
            
            if wave_data and len(wave_data) > 0:
                # CORRECTION: Validation des données numériques
                try:
                    # Filtrer les valeurs non numériques
                    valid_data = [x for x in wave_data if
                                  isinstance(x, (int, float)) and not (x != x)]  # x != x détecte NaN
                    
                    if valid_data:
                        # Calculer les statistiques
                        wave_avg = sum(valid_data) / len(valid_data)
                        wave_max = max(valid_data)
                        wave_min = min(valid_data)
                        
                        # Calcul de l'écart-type
                        if len(valid_data) > 1:
                            variance = sum((x - wave_avg) ** 2 for x in valid_data) / len(valid_data)
                            wave_std = variance ** 0.5
                        else:
                            wave_std = 0
                        
                        row_data.update({
                            f'{wave_type}_avg': round(wave_avg, 6),
                            f'{wave_type}_max': round(wave_max, 6),
                            f'{wave_type}_min': round(wave_min, 6),
                            f'{wave_type}_std': round(wave_std, 6),
                            f'{wave_type}_raw': json.dumps(valid_data[:100])  # CORRECTION: Limiter la taille
                        })
                    else:
                        # Aucune donnée valide
                        row_data.update({
                            f'{wave_type}_avg': '',
                            f'{wave_type}_max': '',
                            f'{wave_type}_min': '',
                            f'{wave_type}_std': '',
                            f'{wave_type}_raw': '[]'
                        })
                except Exception as e:
                    print(f"Erreur traitement onde {wave_type}: {e}")
                    # Valeurs par défaut en cas d'erreur
                    row_data.update({
                        f'{wave_type}_avg': '',
                        f'{wave_type}_max': '',
                        f'{wave_type}_min': '',
                        f'{wave_type}_std': '',
                        f'{wave_type}_raw': '[]'
                    })
            else:
                # Valeurs par défaut si pas de données
                row_data.update({
                    f'{wave_type}_avg': '',
                    f'{wave_type}_max': '',
                    f'{wave_type}_min': '',
                    f'{wave_type}_std': '',
                    f'{wave_type}_raw': '[]'
                })
    
    def _write_csv_row(self, row_data: Dict):
        """CORRECTION: Écrit une ligne dans le CSV avec colonnes simplifiées"""
        if not self.csv_writer:
            return
        
        # CORRECTION: Ordre des colonnes selon les nouveaux headers simplifiés
        ordered_values = [
            row_data.get('timestamp', ''),
            row_data.get('session_duration', ''),
            row_data.get('calm_probability', ''),
            row_data.get('calm_percentage', ''),
            row_data.get('focus_probability', ''),
            row_data.get('focus_percentage', ''),
            row_data.get('attention_probability', ''),
            row_data.get('attention_percentage', ''),
            row_data.get('delta_avg', ''),
            row_data.get('delta_max', ''),
            row_data.get('delta_min', ''),
            row_data.get('delta_std', ''),
            row_data.get('delta_raw', ''),
            row_data.get('theta_avg', ''),
            row_data.get('theta_max', ''),
            row_data.get('theta_min', ''),
            row_data.get('theta_std', ''),
            row_data.get('theta_raw', ''),
            row_data.get('alpha_avg', ''),
            row_data.get('alpha_max', ''),
            row_data.get('alpha_min', ''),
            row_data.get('alpha_std', ''),
            row_data.get('alpha_raw', ''),
            row_data.get('beta_avg', ''),
            row_data.get('beta_max', ''),
            row_data.get('beta_min', ''),
            row_data.get('beta_std', ''),
            row_data.get('beta_raw', ''),
            row_data.get('gamma_avg', ''),
            row_data.get('gamma_max', ''),
            row_data.get('gamma_min', ''),
            row_data.get('gamma_std', ''),
            row_data.get('gamma_raw', '')
        ]
        
        try:
            self.csv_writer.writerow(ordered_values)
            self.csv_file.flush()  # Force l'écriture
        except Exception as e:
            print(f"Erreur écriture ligne CSV: {e}")
    
    def stop_session(self) -> str:
        """Arrête la session d'enregistrement"""
        csv_path = ""
        
        if self.csv_file:
            csv_path = self.csv_file.name
            
            # CORRECTION: Fermeture sécurisée du fichier
            try:
                self.csv_file.close()
            except Exception as e:
                print(f"Erreur fermeture fichier: {e}")
            finally:
                self.csv_file = None
                self.csv_writer = None
            
            print(f"Session d'enregistrement terminée: {csv_path}")
            print(f"Nombre de points de données: {len(self.session_data)}")
            
            # Générer un rapport de session
            try:
                self._generate_session_report(csv_path)
            except Exception as e:
                print(f"Erreur génération rapport: {e}")
        
        return csv_path
    
    def _generate_session_report(self, csv_path: str):
        """Génère un rapport de la session"""
        if not self.session_data or not self.session_start_time:
            return
        
        report_path = csv_path.replace('.csv', '_report.txt')
        
        try:
            # Calculer les statistiques de session
            session_duration = (datetime.now() - self.session_start_time).total_seconds()
            data_points = len(self.session_data)
            
            # CORRECTION: Statistiques des métriques principales avec gestion d'erreurs
            calm_values = []
            focus_values = []
            attention_values = []
            
            for d in self.session_data:
                if d.get('calm_percentage') and isinstance(d.get('calm_percentage'), (int, float)):
                    calm_values.append(d['calm_percentage'])
                if d.get('focus_percentage') and isinstance(d.get('focus_percentage'), (int, float)):
                    focus_values.append(d['focus_percentage'])
                if d.get('attention_percentage') and isinstance(d.get('attention_percentage'), (int, float)):
                    attention_values.append(d['attention_percentage'])
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"=== RAPPORT DE SESSION NEUROSITY ===\n")
                f.write(f"Session: {self.current_session}\n")
                f.write(f"Début: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Durée: {session_duration:.1f} secondes ({session_duration / 60:.1f} minutes)\n")
                f.write(f"Points de données: {data_points}\n\n")
                
                if calm_values:
                    f.write(f"CALME ({len(calm_values)} mesures):\n")
                    f.write(f"  Moyenne: {sum(calm_values) / len(calm_values):.1f}%\n")
                    f.write(f"  Maximum: {max(calm_values):.1f}%\n")
                    f.write(f"  Minimum: {min(calm_values):.1f}%\n\n")
                
                if focus_values:
                    f.write(f"CONCENTRATION ({len(focus_values)} mesures):\n")
                    f.write(f"  Moyenne: {sum(focus_values) / len(focus_values):.1f}%\n")
                    f.write(f"  Maximum: {max(focus_values):.1f}%\n")
                    f.write(f"  Minimum: {min(focus_values):.1f}%\n\n")
                
                if attention_values:
                    f.write(f"ATTENTION ({len(attention_values)} mesures):\n")
                    f.write(f"  Moyenne: {sum(attention_values) / len(attention_values):.1f}%\n")
                    f.write(f"  Maximum: {max(attention_values):.1f}%\n")
                    f.write(f"  Minimum: {min(attention_values):.1f}%\n\n")
                
                # CORRECTION: Statistiques des ondes cérébrales
                f.write(f"ONDES CÉRÉBRALES:\n")
                wave_stats_found = False
                for wave_type in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                    wave_avgs = []
                    for d in self.session_data:
                        wave_avg = d.get(f'{wave_type}_avg')
                        if wave_avg and isinstance(wave_avg, (int, float)):
                            wave_avgs.append(wave_avg)
                    
                    if wave_avgs:
                        wave_stats_found = True
                        f.write(f"  {wave_type.title()} ({len(wave_avgs)} mesures):\n")
                        f.write(f"    Moyenne: {sum(wave_avgs) / len(wave_avgs):.3f} μV\n")
                        f.write(f"    Maximum: {max(wave_avgs):.3f} μV\n")
                        f.write(f"    Minimum: {min(wave_avgs):.3f} μV\n")
                
                if not wave_stats_found:
                    f.write("  Aucune donnée d'ondes cérébrales collectée\n")
            
            print(f"Rapport généré: {report_path}")
        
        except Exception as e:
            print(f"Erreur génération rapport: {e}")
    
    def get_session_list(self) -> List[str]:
        """Retourne la liste des sessions disponibles"""
        try:
            csv_files = [f for f in os.listdir(self.data_directory)
                         if f.endswith('.csv') and os.path.isfile(os.path.join(self.data_directory, f))]
            return sorted(csv_files, reverse=True)  # Plus récentes en premier
        except Exception as e:
            print(f"Erreur liste sessions: {e}")
            return []
    
    def analyze_session(self, csv_filename: str) -> Dict:
        """Analyse une session enregistrée"""
        csv_path = os.path.join(self.data_directory, csv_filename)
        
        if not os.path.exists(csv_path):
            return {'error': 'Fichier non trouvé'}
        
        try:
            # CORRECTION: Lire le CSV avec gestion d'erreurs robuste
            try:
                df = pd.read_csv(csv_path, delimiter=';')
            except Exception as e:
                # Fallback avec délimiteur virgule
                print(f"Erreur lecture avec ';', essai avec ',': {e}")
                df = pd.read_csv(csv_path, delimiter=',')
            
            if df.empty:
                return {'error': 'Fichier CSV vide'}
            
            analysis = {
                'filename': csv_filename,
                'total_points': len(df),
                'duration': float(df['session_duration'].max()) if 'session_duration' in df and not df[
                    'session_duration'].isna().all() else 0,
                'start_time': str(df['timestamp'].iloc[0]) if len(df) > 0 and 'timestamp' in df else '',
                'end_time': str(df['timestamp'].iloc[-1]) if len(df) > 0 and 'timestamp' in df else '',
            }
            
            # Analyses des métriques principales avec gestion d'erreurs
            for metric in ['calm_percentage', 'focus_percentage', 'attention_percentage']:
                if metric in df and not df[metric].isna().all():
                    try:
                        values = pd.to_numeric(df[metric], errors='coerce').dropna()
                        if len(values) > 0:
                            analysis[metric] = {
                                'mean': float(values.mean()),
                                'std': float(values.std()) if len(values) > 1 else 0,
                                'min': float(values.min()),
                                'max': float(values.max()),
                                'count': len(values)
                            }
                    except Exception as e:
                        print(f"Erreur analyse métrique {metric}: {e}")
            
            # CORRECTION: Analyse des ondes cérébrales
            for wave_type in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                avg_col = f'{wave_type}_avg'
                if avg_col in df and not df[avg_col].isna().all():
                    try:
                        values = pd.to_numeric(df[avg_col], errors='coerce').dropna()
                        if len(values) > 0:
                            analysis[f'{wave_type}_wave'] = {
                                'mean': float(values.mean()),
                                'std': float(values.std()) if len(values) > 1 else 0,
                                'min': float(values.min()),
                                'max': float(values.max()),
                                'count': len(values)
                            }
                    except Exception as e:
                        print(f"Erreur analyse onde {wave_type}: {e}")
            
            return analysis
        
        except Exception as e:
            print(f"Erreur analyse session: {e}")
            return {'error': str(e)}
    
    def export_session_summary(self, csv_filename: str) -> str:
        """Exporte un résumé de session en format JSON"""
        analysis = self.analyze_session(csv_filename)
        
        if 'error' in analysis:
            return ""
        
        try:
            json_filename = csv_filename.replace('.csv', '_summary.json')
            json_path = os.path.join(self.data_directory, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
            
            return json_path
        except Exception as e:
            print(f"Erreur export JSON: {e}")
            return ""
    
    def cleanup_old_sessions(self, days_to_keep: int = 30):
        """CORRECTION: Supprime les sessions anciennes pour économiser l'espace"""
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
                        # Supprimer aussi le rapport s'il existe
                        report_path = session_path.replace('.csv', '_report.txt')
                        if os.path.exists(report_path):
                            os.remove(report_path)
                        deleted_count += 1
                        print(f"Session supprimée: {session}")
                except Exception as e:
                    print(f"Erreur suppression {session}: {e}")
            
            if deleted_count > 0:
                print(f"Nettoyage terminé: {deleted_count} session(s) supprimée(s)")
        
        except Exception as e:
            print(f"Erreur nettoyage: {e}")
    
    def get_storage_info(self) -> Dict:
        """CORRECTION: Retourne des informations sur l'espace de stockage utilisé"""
        try:
            total_size = 0
            file_count = 0
            
            for filename in os.listdir(self.data_directory):
                file_path = os.path.join(self.data_directory, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
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