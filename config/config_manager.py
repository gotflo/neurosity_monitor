#!/usr/bin/env python3
"""
Gestionnaire de configuration sécurisé pour Neurosity Monitor
Stockage chiffré des identifiants dans un fichier local
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Gestionnaire de configuration avec chiffrement"""
    
    def __init__(self, config_path: str = "config/user_config.enc"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clé de chiffrement dérivée du système
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Configuration par défaut
        self.default_config = {
            "device_id": "",
            "email": "",
            "password": "",
            "auto_connect": False,
            "remember_credentials": True,
            "last_updated": None
        }
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Génère ou récupère la clé de chiffrement"""
        key_file = Path("config/.key")
        key_file.parent.mkdir(parents=True, exist_ok=True)
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Générer une nouvelle clé
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Protéger le fichier (Unix uniquement)
            try:
                os.chmod(key_file, 0o600)
            except:
                pass
            
            return key
    
    def save_config(self, config: Dict) -> bool:
        """Sauvegarde la configuration de manière chiffrée"""
        try:
            # Ajouter la date de mise à jour
            from datetime import datetime
            config['last_updated'] = datetime.now().isoformat()
            
            # Convertir en JSON
            json_data = json.dumps(config, indent=2)
            
            # Chiffrer
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            # Sauvegarder
            with open(self.config_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Protéger le fichier
            try:
                os.chmod(self.config_path, 0o600)
            except:
                pass
            
            logger.info(f"Configuration sauvegardée: {self.config_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration: {e}")
            return False
    
    def load_config(self) -> Dict:
        """Charge la configuration chiffrée"""
        try:
            if not self.config_path.exists():
                logger.info("Aucune configuration sauvegardée, utilisation des valeurs par défaut")
                return self.default_config.copy()
            
            # Lire le fichier chiffré
            with open(self.config_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Déchiffrer
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            # Parser JSON
            config = json.loads(decrypted_data.decode())
            
            # Fusionner avec les valeurs par défaut pour les nouvelles clés
            final_config = self.default_config.copy()
            final_config.update(config)
            
            logger.info("Configuration chargée avec succès")
            return final_config
        
        except Exception as e:
            logger.error(f"Erreur chargement configuration: {e}")
            return self.default_config.copy()
    
    def get_neurosity_credentials(self) -> Dict[str, str]:
        """Récupère les identifiants Neurosity"""
        config = self.load_config()
        
        return {
            'device_id': config.get('device_id', ''),
            'email': config.get('email', ''),
            'password': config.get('password', '')
        }
    
    def update_credentials(self, device_id: str, email: str, password: str,
                           auto_connect: bool = False, remember: bool = True) -> bool:
        """Met à jour les identifiants"""
        config = self.load_config()
        
        config['device_id'] = device_id
        config['email'] = email
        
        # Ne sauvegarder le mot de passe que si "remember" est activé
        if remember:
            config['password'] = password
        else:
            config['password'] = ""
        
        config['auto_connect'] = auto_connect
        config['remember_credentials'] = remember
        
        return self.save_config(config)
    
    def clear_credentials(self) -> bool:
        """Efface les identifiants sauvegardés"""
        config = self.default_config.copy()
        return self.save_config(config)
    
    def get_current_config(self) -> Dict:
        """Récupère la configuration actuelle (sans le mot de passe en clair)"""
        config = self.load_config()
        
        # Masquer le mot de passe
        display_config = config.copy()
        if display_config.get('password'):
            display_config['password'] = '•' * 8
        
        return display_config
    
    def test_connection(self, device_id: str, email: str, password: str) -> Dict:
        """Teste la connexion avec les identifiants fournis"""
        try:
            from neurosity import NeurositySDK
            
            neurosity = NeurositySDK({"device_id": device_id})
            
            result = neurosity.login({
                "email": email,
                "password": password
            })
            
            # Déconnexion immédiate
            neurosity.logout()
            
            return {
                'success': True,
                'message': 'Connexion réussie !'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def migrate_from_env(self) -> bool:
        """Migre la configuration depuis le .env vers le stockage chiffré"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            device_id = os.getenv('NEUROSITY_DEVICE_ID', '')
            email = os.getenv('NEUROSITY_EMAIL', '')
            password = os.getenv('NEUROSITY_PASSWORD', '')
            
            if device_id and email and password:
                return self.update_credentials(
                    device_id=device_id,
                    email=email,
                    password=password,
                    auto_connect=False,
                    remember=True
                )
            
            return False
        
        except Exception as e:
            logger.error(f"Erreur migration .env: {e}")
            return False


# Instance globale
config_manager = ConfigManager()