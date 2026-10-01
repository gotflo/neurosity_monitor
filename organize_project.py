#!/usr/bin/env python3
"""
NEUROSITY MONITOR - ORGANISATEUR DE PROJET
Organise automatiquement les fichiers dans la bonne structure
avant la compilation PyInstaller
"""

import os
import shutil
from pathlib import Path


def create_directory_structure():
    """Crée la structure de dossiers nécessaire"""
    directories = [
        'templates',
        'templates/components',
        'static',
        'static/css',
        'static/js',
        'static/assets',
        'config',
        'utils',
        'data',
        'logs',
        'recordings',
    ]
    
    print("\n" + "="*60)
    print("CRÉATION DE LA STRUCTURE DE DOSSIERS")
    print("="*60 + "\n")
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ {directory}/")
    
    # Créer __init__.py pour les packages Python
    for package in ['config', 'utils']:
        init_file = Path(package) / '__init__.py'
        init_file.touch()
        print(f"✓ {init_file}")


def organize_files():
    """Organise les fichiers dans la bonne structure"""
    print("\n" + "="*60)
    print("ORGANISATION DES FICHIERS")
    print("="*60 + "\n")
    
    # Mapping: fichier source -> destination
    file_mappings = {
        # Templates HTML
        'index.html': 'templates/index.html',
        'settings.html': 'templates/settings.html',
        
        # CSS
        'main.css': 'static/css/main.css',
        'settings.css': 'static/css/settings.css',
        
        # JavaScript
        'app.js': 'static/js/app.js',
        'settings.js': 'static/js/settings.js',
        
        # Configuration
        'config_manager.py': 'config/config_manager.py',
        'settings.py': 'config/settings.py',
        
        # Utilitaires
        'neurosity_helper.py': 'utils/neurosity_helper.py',
    }
    
    copied_count = 0
    skipped_count = 0
    
    for source, destination in file_mappings.items():
        source_path = Path(source)
        dest_path = Path(destination)
        
        if source_path.exists():
            # Copier le fichier
            shutil.copy2(source_path, dest_path)
            print(f"✓ {source} → {destination}")
            copied_count += 1
        else:
            print(f"⚠ {source} (non trouvé, ignoré)")
            skipped_count += 1
    
    print(f"\nFichiers copiés: {copied_count}")
    print(f"Fichiers ignorés: {skipped_count}")


def verify_structure():
    """Vérifie que la structure est correcte"""
    print("\n" + "="*60)
    print("VÉRIFICATION DE LA STRUCTURE")
    print("="*60 + "\n")
    
    # Fichiers essentiels
    essential_files = {
        'Python': [
            'app.py',
            'data_manager.py',
            'neurosity_worker.py',
            'config/config_manager.py',
            'config/settings.py',
            'utils/neurosity_helper.py',
        ],
        'Templates': [
            'templates/index.html',
            'templates/settings.html',
        ],
        'Static CSS': [
            'static/css/main.css',
            'static/css/settings.css',
        ],
        'Static JS': [
            'static/js/app.js',
            'static/js/settings.js',
        ],
        'Build': [
            'neurosity_monitor.spec',
            'requirements.txt',
            'build.bat',
        ],
    }
    
    all_ok = True
    
    for category, files in essential_files.items():
        print(f"{category}:")
        category_ok = True
        
        for file_path in files:
            exists = Path(file_path).exists()
            symbol = "✓" if exists else "✗"
            status = "OK" if exists else "MANQUANT"
            print(f"  {symbol} {file_path} ({status})")
            
            if not exists:
                category_ok = False
                all_ok = False
        
        if category_ok:
            print(f"  → {category}: Complet")
        else:
            print(f"  → {category}: Incomplet")
        print()
    
    return all_ok


def create_env_template():
    """Crée un fichier .env.template"""
    env_template = """# ============================================
# NEUROSITY MONITOR - CONFIGURATION
# ============================================
#
# IMPORTANT: Renommez ce fichier en .env
# et remplissez vos informations
#
# OU utilisez l'interface Settings dans l'application
# (recommandé - configuration chiffrée)
# ============================================

NEUROSITY_EMAIL=votre.email@example.com
NEUROSITY_PASSWORD=votre_mot_de_passe
NEUROSITY_DEVICE_ID=votre_device_id

FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# ============================================
# NOTES
# ============================================
#
# 1. Device ID: Trouvez-le dans l'app Neurosity
# 2. Email/Password: Vos identifiants Neurosity
# 3. L'interface Settings est plus sécurisée
#    (stockage chiffré des credentials)
#
# ============================================
"""
    
    with open('.env.template', 'w', encoding='utf-8') as f:
        f.write(env_template)
    
    print("✓ .env.template créé")


def create_gitignore():
    """Crée un .gitignore approprié"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/

# PyInstaller
build/
dist/
*.spec

# Logs
*.log
logs/

# Data
data/
recordings/
*.csv

# Configuration
.env
config/.key
config/user_config.enc

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary
*.tmp
*.bak
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("✓ .gitignore créé")


def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("NEUROSITY MONITOR - ORGANISATEUR DE PROJET")
    print("="*60)
    
    try:
        # 1. Créer la structure de dossiers
        create_directory_structure()
        
        # 2. Organiser les fichiers
        organize_files()
        
        # 3. Créer fichiers additionnels
        print("\n" + "="*60)
        print("CRÉATION FICHIERS ADDITIONNELS")
        print("="*60 + "\n")
        create_env_template()
        create_gitignore()
        
        # 4. Vérifier la structure
        structure_ok = verify_structure()
        
        # 5. Résumé
        print("\n" + "="*60)
        if structure_ok:
            print("✓ STRUCTURE PRÊTE POUR LA COMPILATION")
            print("="*60 + "\n")
            print("Prochaines étapes:")
            print("  1. Vérifiez que tous les fichiers sont présents")
            print("  2. Exécutez: build.bat")
            print("  3. Ou manuellement: pyinstaller neurosity_monitor.spec --clean")
        else:
            print("⚠ STRUCTURE INCOMPLÈTE")
            print("="*60 + "\n")
            print("Certains fichiers sont manquants.")
            print("Vérifiez les fichiers marqués comme MANQUANT ci-dessus.")
        print("="*60 + "\n")
        
        return structure_ok
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
