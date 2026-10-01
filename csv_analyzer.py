#!/usr/bin/env python3
"""
Module d'analyse et de visualisation des données Neurosity CSV
Calcule toutes les métriques cognitives dérivées et prépare les données pour la visualisation
"""

import csv
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging

from i18n import t as _t

logger = logging.getLogger(__name__)


class NeurosityCSVAnalyzer:
    """Analyseur de fichiers CSV Neurosity avec calcul de métriques dérivées"""
    
    ELECTRODES = ['CP3', 'C3', 'F5', 'PO3', 'PO4', 'F6', 'C4', 'CP4']
    BANDS = ['delta', 'theta', 'alpha', 'beta', 'gamma']
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.data = []
        self.timestamps = []
    
    def load_and_analyze(self) -> Dict[str, Any]:
        """Charge et analyse le fichier CSV complet"""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"{_t('file_not_found')}: {self.csv_path}")
        
        try:
            # Charger les données
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    self.data.append(row)
                    if row.get('timestamp'):
                        self.timestamps.append(row['timestamp'])
            
            if not self.data:
                raise ValueError(_t('empty_csv'))
            
            # Préparer toutes les analyses
            result = {
                'filename': self.csv_path.name,
                'total_points': len(self.data),
                'duration': self._get_duration(),
                'timestamps': self.timestamps,
                
                # États cognitifs
                'cognitive_states': self._extract_cognitive_states(),
                
                # Bandes de fréquences par électrode
                'frequency_bands': self._extract_frequency_bands(),
                
                # Signaux EEG bruts
                'eeg_raw': self._extract_eeg_raw(),
                
                # Métriques dérivées
                'derived_metrics': self._calculate_derived_metrics(),
                
                # Statistiques globales
                'statistics': self._calculate_statistics()
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Erreur analyse CSV: {e}")
            raise
    
    def _get_duration(self) -> float:
        """Obtient la durée totale de la session"""
        if self.data and self.data[-1].get('session_duration'):
            try:
                return float(self.data[-1]['session_duration'])
            except:
                pass
        return 0.0
    
    def _extract_cognitive_states(self) -> Dict[str, List[float]]:
        """Extrait les données d'état cognitif (calm et focus)"""
        calm = []
        focus = []
        
        for row in self.data:
            try:
                calm_val = float(row.get('calm_probability', 0)) if row.get('calm_probability') else None
                focus_val = float(row.get('focus_probability', 0)) if row.get('focus_probability') else None
                
                calm.append(calm_val)
                focus.append(focus_val)
            except:
                calm.append(None)
                focus.append(None)
        
        return {
            'calm': calm,
            'focus': focus
        }
    
    def _extract_frequency_bands(self) -> Dict[str, Dict[str, List[float]]]:
        """Extrait toutes les bandes de fréquences par électrode"""
        bands_data = {}
        
        for band in self.BANDS:
            bands_data[band] = {}
            for electrode in self.ELECTRODES:
                key = f'{band}_{electrode}'
                values = []
                
                for row in self.data:
                    try:
                        val = float(row.get(key, 0)) if row.get(key) else None
                        values.append(val)
                    except:
                        values.append(None)
                
                bands_data[band][electrode] = values
        
        return bands_data
    
    def _extract_eeg_raw(self) -> Dict[str, List[float]]:
        """Extrait les signaux EEG bruts"""
        eeg_data = {}
        
        for electrode in self.ELECTRODES:
            key = f'eeg_{electrode}'
            values = []
            
            for row in self.data:
                try:
                    val = float(row.get(key, 0)) if row.get(key) else None
                    values.append(val)
                except:
                    values.append(None)
            
            eeg_data[electrode] = values
        
        return eeg_data
    
    def _calculate_derived_metrics(self) -> Dict[str, List[float]]:
        """Calcule toutes les métriques dérivées/interprétatives avec les formules correctes"""
        metrics = {}
        
        # Extraire les données nécessaires
        bands = self._extract_frequency_bands()
        
        # Calculer les moyennes par bande pour chaque point temporel
        n_points = len(self.data)
        
        # Initialiser les arrays
        theta_avg = np.zeros(n_points)
        alpha_avg = np.zeros(n_points)
        beta_avg = np.zeros(n_points)
        gamma_avg = np.zeros(n_points)
        delta_avg = np.zeros(n_points)
        
        # Calculer les moyennes
        for i in range(n_points):
            theta_vals = [bands['theta'][e][i] for e in self.ELECTRODES if bands['theta'][e][i] is not None]
            alpha_vals = [bands['alpha'][e][i] for e in self.ELECTRODES if bands['alpha'][e][i] is not None]
            beta_vals = [bands['beta'][e][i] for e in self.ELECTRODES if bands['beta'][e][i] is not None]
            gamma_vals = [bands['gamma'][e][i] for e in self.ELECTRODES if bands['gamma'][e][i] is not None]
            delta_vals = [bands['delta'][e][i] for e in self.ELECTRODES if bands['delta'][e][i] is not None]
            
            theta_avg[i] = np.mean(theta_vals) if theta_vals else 0
            alpha_avg[i] = np.mean(alpha_vals) if alpha_vals else 0
            beta_avg[i] = np.mean(beta_vals) if beta_vals else 0
            gamma_avg[i] = np.mean(gamma_vals) if gamma_vals else 0
            delta_avg[i] = np.mean(delta_vals) if delta_vals else 0
        
        # ============================================
        # FORMULES CORRIGÉES
        # ============================================
        
        # 1. Theta/Beta Ratio (TBR) - Baisse d'attention
        # TBR élevé → baisse d'attention, distractibilité, fatigue
        # TBR faible → attention soutenue
        theta_beta_ratio = []
        for i in range(n_points):
            if beta_avg[i] > 0:
                ratio = theta_avg[i] / beta_avg[i]
                theta_beta_ratio.append(ratio)
            else:
                theta_beta_ratio.append(None)
        
        metrics['theta_beta_ratio'] = theta_beta_ratio

        # 1b. Delta/Beta Ratio - Charge affective (Affective Load)
        # Élevé → sujet déconnecté de l'activité cognitive, cerveau en réseau par défaut
        # Bas → éveil, activité cognitive
        delta_beta_ratio = []
        for i in range(n_points):
            if beta_avg[i] > 0:
                ratio = delta_avg[i] / beta_avg[i]
                delta_beta_ratio.append(ratio)
            else:
                delta_beta_ratio.append(None)

        metrics['delta_beta_ratio'] = delta_beta_ratio
        
        # 2. Engagement Index (Pope et al. 1995)
        # Engagement = Beta / (Alpha + Theta)
        # Élevé → engagement cognitif, vigilance, concentration active
        # Bas → désengagement, fatigue, rêverie
        engagement = []
        for i in range(n_points):
            denom = alpha_avg[i] + theta_avg[i]
            if denom > 0:
                eng = beta_avg[i] / denom
                engagement.append(eng)
            else:
                engagement.append(None)
        
        metrics['engagement'] = engagement
        
        # 3. Alpha/Theta Ratio - Fatigue
        # Faible → fatigue, somnolence, baisse d'attention
        # Élevé → relaxation mais vigilance stable
        alpha_theta_ratio = []
        for i in range(n_points):
            if theta_avg[i] > 0:
                ratio = alpha_avg[i] / theta_avg[i]
                alpha_theta_ratio.append(ratio)
            else:
                alpha_theta_ratio.append(None)
        
        metrics['alpha_theta_ratio'] = alpha_theta_ratio
        
        # 4. Beta/Alpha Ratio - Vigilance
        # Élevé → vigilance élevée, tension mentale
        # Bas → relaxation, calme
        alpha_beta_ratio = []
        for i in range(n_points):
            if alpha_avg[i] > 0:
                ratio = beta_avg[i] / alpha_avg[i]
                alpha_beta_ratio.append(ratio)
            else:
                alpha_beta_ratio.append(None)
        
        metrics['beta_alpha_ratio'] = alpha_beta_ratio
        
        # 5. Charge cognitive (Cognitive Load) — Theta / Alpha
        # Réf. : Task Load Index (Gevins) ; Raufi & Longo (2022).
        # On ne met pas Beta au dénominateur : Beta monte en activité cognitive,
        # donc Theta/Beta baisse quand la charge augmente (l'inverse de ce qu'on veut montrer).
        # Élevé → charge cognitive importante
        cognitive_load = []
        for i in range(n_points):
            if alpha_avg[i] > 0:
                load = theta_avg[i] / alpha_avg[i]
                cognitive_load.append(load)
            else:
                cognitive_load.append(None)
        
        metrics['cognitive_load'] = cognitive_load
        
        # 6. Indice de relaxation — Alpha / (Beta + Gamma)
        # NOTE : la convention de la littérature (Putman, MDPI 2023, etc.) est α/β seul.
        # Inclure γ (>30 Hz) est risqué sur le Crown car cette bande est fortement contaminée
        # par l'EMG (mâchoire, sourcils) → peut artificiellement faire chuter l'indice.
        # Élevé → relaxation, méditation
        # Bas → tension, stress
        relaxation = []
        for i in range(n_points):
            denom = beta_avg[i] + gamma_avg[i]
            if denom > 0:
                relax = alpha_avg[i] / denom
                relaxation.append(relax)
            else:
                relaxation.append(None)
        
        metrics['relaxation'] = relaxation
        
        # 7. Indice de ralentissement EEG / Drowsiness Index — (Delta+Theta)/(Alpha+Beta)
        # Réf. : Jap, Lal, Fischer & Bekiaris (2009) ; Eoh, Chung & Kim (2005).
        # ATTENTION : « activation level » est trompeur — l'indice MONTE quand le sujet
        #   se DÉSACTIVE (somnolence). Plus précisément :
        #   Élevé → ondes lentes dominantes → vigilance basse / somnolence
        #   Bas   → ondes rapides dominantes → activation cognitive élevée
        activation_level = []
        for i in range(n_points):
            denom = alpha_avg[i] + beta_avg[i]
            if denom > 0:
                level = (delta_avg[i] + theta_avg[i]) / denom
                activation_level.append(level)
            else:
                activation_level.append(None)
        
        metrics['activation_level'] = activation_level
        
        # 8. Stress Index - moyenne Gamma frontal (F5, F6)
        stress = []
        for i in range(n_points):
            f5_gamma = bands['gamma']['F5'][i]
            f6_gamma = bands['gamma']['F6'][i]
            
            vals = [v for v in [f5_gamma, f6_gamma] if v is not None]
            if vals:
                stress.append(np.mean(vals))
            else:
                stress.append(None)
        
        metrics['stress'] = stress
        
        # 9-11. Asymétries EEG — convention Davidson / Allen, Coan & Nazarian (2004)
        # FAA = ln(alpha_droite) - ln(alpha_gauche)   (ex: lnF6 - lnF5)
        # L'alpha est inversement lié à l'activité corticale, donc :
        #   FAA > 0  → plus d'alpha à droite → activité GAUCHE dominante → approche / affect positif (BAS)
        #   FAA < 0  → plus d'alpha à gauche → activité DROITE dominante → retrait / affect négatif (BIS)
        # Électrodes Crown : impaires = gauche (F5, C3, PO3), paires = droite (F6, C4, PO4).

        # Asymétrie frontale (F6 - F5)
        asymmetry_f5_f6 = []
        for i in range(n_points):
            f5_alpha = bands['alpha']['F5'][i]
            f6_alpha = bands['alpha']['F6'][i]

            if f5_alpha is not None and f6_alpha is not None and f5_alpha > 0 and f6_alpha > 0:
                asym = np.log(f6_alpha) - np.log(f5_alpha)
                asymmetry_f5_f6.append(asym)
            else:
                asymmetry_f5_f6.append(None)

        metrics['asymmetry_frontal'] = asymmetry_f5_f6

        # Asymétrie centrale (C4 - C3)
        asymmetry_c3_c4 = []
        for i in range(n_points):
            c3_alpha = bands['alpha']['C3'][i]
            c4_alpha = bands['alpha']['C4'][i]

            if c3_alpha is not None and c4_alpha is not None and c3_alpha > 0 and c4_alpha > 0:
                asym = np.log(c4_alpha) - np.log(c3_alpha)
                asymmetry_c3_c4.append(asym)
            else:
                asymmetry_c3_c4.append(None)

        metrics['asymmetry_central'] = asymmetry_c3_c4

        # Asymétrie pariétale (PO4 - PO3)
        asymmetry_po3_po4 = []
        for i in range(n_points):
            po3_alpha = bands['alpha']['PO3'][i]
            po4_alpha = bands['alpha']['PO4'][i]

            if po3_alpha is not None and po4_alpha is not None and po3_alpha > 0 and po4_alpha > 0:
                asym = np.log(po4_alpha) - np.log(po3_alpha)
                asymmetry_po3_po4.append(asym)
            else:
                asymmetry_po3_po4.append(None)
        
        metrics['asymmetry_parietal'] = asymmetry_po3_po4
        
        # 12. Puissances relatives (pourcentage de chaque bande)
        total_power = delta_avg + theta_avg + alpha_avg + beta_avg + gamma_avg
        
        for band_name, band_avg in [
            ('delta', delta_avg),
            ('theta', theta_avg),
            ('alpha', alpha_avg),
            ('beta', beta_avg),
            ('gamma', gamma_avg)
        ]:
            relative_power = []
            for i in range(n_points):
                if total_power[i] > 0:
                    rel = (band_avg[i] / total_power[i]) * 100
                    relative_power.append(rel)
                else:
                    relative_power.append(None)
            
            metrics[f'{band_name}_relative'] = relative_power
        
        return metrics
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calcule des statistiques globales"""
        stats = {}
        
        # Stats pour calm et focus
        cognitive = self._extract_cognitive_states()
        for metric_name, values in cognitive.items():
            valid_vals = [v for v in values if v is not None]
            if valid_vals:
                stats[metric_name] = {
                    'mean': float(np.mean(valid_vals)),
                    'std': float(np.std(valid_vals)),
                    'min': float(np.min(valid_vals)),
                    'max': float(np.max(valid_vals))
                }
        
        # Stats pour les bandes de fréquences
        bands = self._extract_frequency_bands()
        for band in self.BANDS:
            all_values = []
            for electrode in self.ELECTRODES:
                values = [v for v in bands[band][electrode] if v is not None]
                all_values.extend(values)
            
            if all_values:
                stats[f'{band}_power'] = {
                    'mean': float(np.mean(all_values)),
                    'std': float(np.std(all_values)),
                    'min': float(np.min(all_values)),
                    'max': float(np.max(all_values))
                }
        
        return stats


def analyze_csv_file(csv_path: str) -> Dict[str, Any]:
    """
    Fonction helper pour analyser un fichier CSV

    Args:
        csv_path: Chemin vers le fichier CSV

    Returns:
        Dictionnaire contenant toutes les analyses
    """
    analyzer = NeurosityCSVAnalyzer(csv_path)
    return analyzer.load_and_analyze()