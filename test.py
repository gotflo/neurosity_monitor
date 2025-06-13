"""
Script d'installation automatique pour Neurosity Monitor
Installe et configure automatiquement l'application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import shutil
import json


class NeurosityInstaller2:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.python_executable = sys.executable
        self.platform = platform.system().lower()

    def print_header(self):
        """Affiche l'en-tête du script d'installation"""
        print("=" * 60)
        print("🧠 NEUROSITY MONITOR - INSTALLATION")
        print("=" * 60)
        print(f"Plateforme: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Répertoire: {self.project_dir}")
        print("=" * 60)

    def check_python_version(self):
        """Vérifie la version de Python"""
        print("🐍 Vérification de la version Python...")

        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ requis")
            print(f"Version actuelle: {sys.version}")
            return False

        print(f"✅ Python {sys.version.split()[0]} - OK")
        return True

    def check_dependencies(self):
        """Vérifie les dépendances système"""
        print("\n📦 Vérification des dépendances système...")

        # Vérifier pip
        try:
            subprocess.run([self.python_executable, "-m", "pip", "--version"],
                           check=True, capture_output=True)
            print("✅ pip - OK")
        except subprocess.CalledProcessError:
            print("❌ pip non disponible")
            return False

        # Vérifier git (optionnel)
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            print("✅ git - OK")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  git non disponible (optionnel)")

        return True

    
    def create_env_file(self):
        """Crée le fichier .env avec configuration interactive"""
        env_file = self.project_dir / ".env"

        if env_file.exists():
            print(f"\n⚠️  Fichier .env existant trouvé")
            response = input("Voulez-vous le reconfigurer ? (y/N): ")
            if response.lower() != 'y':
                return True

        print("\n🔧 Configuration de l'environnement...")
        print("Veuillez entrer vos informations Neurosity:")

        # Demander les informations
        email = input("Email Neurosity: ").strip()
        password = input("Mot de passe Neurosity: ").strip()
        device_id = input("Device ID: ").strip()

        if not email or not password or not device_id:
            print("❌ Toutes les informations sont requises")
            return False

        # Configuration avancée
        print("\nConfiguration avancée (appuyez sur Entrée pour les valeurs par défaut):")
        flask_host = input("Host Flask (0.0.0.0): ").strip() or "0.0.0.0"
        flask_port = input("Port Flask (5000): ").strip() or "5000"
        flask_debug = input("Mode debug (False): ").strip() or "False"

        # Contenu du fichier .env
        env_content = f"""# Configuration Neurosity Crown
NEUROSITY_EMAIL={email}
NEUROSITY_PASSWORD={password}
NEUROSITY_DEVICE_ID={device_id}

# Configuration Flask
FLASK_HOST={flask_host}
FLASK_PORT={flask_port}
FLASK_DEBUG={flask_debug}
FLASK_ENV=development

# Configuration de sécurité
SECRET_KEY=neurosity_monitor_secret_key_change_in_production

# Configuration des données
CSV_DELIMITER=;
MAX_CHART_POINTS=50
CHART_UPDATE_INTERVAL=1.0

# Configuration logging
LOG_LEVEL=INFO
"""

        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            print("✅ Fichier .env créé")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la création du fichier .env: {e}")
            return False

    def test_installation(self):
        """Teste si l'installation est fonctionnelle (placeholder)"""
        print("\n🧪 Test de l'installation (à implémenter si besoin)...")
        return True

    def print_completion_message(self):
        print("\n🎉 Installation terminée avec succès !")
        print("Vous pouvez maintenant lancer l'application avec votre commande Flask ou autre.")

    def run2(self):
        """Lance l'installation complète"""
        try:
            self.print_header()

            if not self.check_python_version():
                return False

            if not self.create_env_file():
                return False

            if not self.test_installation():
                print("⚠️  Installation terminée avec des avertissements")

            self.print_completion_message()
            return True

        except KeyboardInterrupt:
            print("\n\n❌ Installation interrompue par l'utilisateur")
            return False
        except Exception as e:
            print(f"\n❌ Erreur inattendue: {e}")
            return False


def main():
    """Fonction principale"""
    installer2 = NeurosityInstaller2()
    success = installer2.run2()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
