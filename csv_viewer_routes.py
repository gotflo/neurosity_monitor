#!/usr/bin/env python3
"""
Routes Flask pour la visualisation des fichiers CSV Neurosity
À intégrer dans app.py
"""

from flask import render_template, jsonify, send_from_directory
from pathlib import Path
import logging

from i18n import t as _t

logger = logging.getLogger(__name__)


def register_csv_viewer_routes(app, data_directory='data'):
    """
    Enregistre les routes de visualisation CSV dans l'application Flask

    Args:
        app: Instance Flask
        data_directory: Chemin vers le dossier des données
    """
    
    @app.route('/viewer')
    def csv_viewer():
        """Page de visualisation CSV"""
        try:
            return render_template('viewer.html')
        except Exception as e:
            logger.error(f"Erreur chargement viewer: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analyze_csv/<filename>')
    def analyze_csv(filename):
        """
        API pour analyser un fichier CSV et retourner toutes les données

        Args:
            filename: Nom du fichier CSV à analyser

        Returns:
            JSON contenant toutes les analyses
        """
        try:
            # Importer le module d'analyse
            from csv_analyzer import analyze_csv_file
            
            # Construire le chemin du fichier
            csv_path = Path(data_directory) / filename
            
            if not csv_path.exists():
                return jsonify({
                    'error': f"{_t('file_not_found')}: {filename}",
                    'code': 'file_not_found'
                }), 404
            
            # Analyser le fichier
            analysis = analyze_csv_file(str(csv_path))
            
            logger.info(f"Analyse CSV réussie: {filename}")
            return jsonify(analysis)
        
        except Exception as e:
            logger.error(f"Erreur analyse CSV {filename}: {e}")
            return jsonify({'error': str(e)}), 500


# Instructions d'intégration dans app.py
INTEGRATION_CODE = """
# Ajouter après l'importation des autres modules (ligne ~40)
from csv_viewer_routes import register_csv_viewer_routes

# Ajouter après la création de l'app Flask (ligne ~122)
# Enregistrer les routes de visualisation CSV
register_csv_viewer_routes(app, data_directory=data_directory)
"""