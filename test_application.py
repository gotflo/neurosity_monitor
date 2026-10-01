#!/usr/bin/env python3
"""
NEUROSITY MONITOR - SCRIPT DE TEST AUTOMATIQUE
Vérifie que l'application compilée fonctionne correctement
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path


class TestRunner:
    """Classe pour exécuter les tests de l'application"""
    
    def __init__(self, dist_path):
        self.dist_path = Path(dist_path)
        # L'exe porte le même nom que son dossier (ex: 01_10_26_NeurosityMonitor)
        self.exe_path = self.dist_path / f"{self.dist_path.name}.exe"
        self.process = None
        # 127.0.0.1 plutôt que localhost : sous Windows, localhost tente d'abord
        # l'IPv6 et chaque requête perd ~2 s avant de retomber sur l'IPv4
        self.base_url = "http://127.0.0.1:5000"
        
    def print_header(self, text):
        """Affiche un en-tête formaté"""
        print("\n" + "="*60)
        print(f" {text}")
        print("="*60 + "\n")
    
    def print_test(self, test_name, passed, message=""):
        """Affiche le résultat d'un test"""
        symbol = "✓" if passed else "✗"
        status = "PASS" if passed else "FAIL"
        
        if message:
            print(f"  {symbol} {test_name}: {status} - {message}")
        else:
            print(f"  {symbol} {test_name}: {status}")
        
        return passed
    
    def test_files_exist(self):
        """Test 1: Vérifier que tous les fichiers nécessaires existent"""
        self.print_header("TEST 1: Fichiers et Structure")
        
        all_ok = True
        
        # Fichiers essentiels
        essential_files = [
            self.exe_path,
            self.dist_path / "_internal",
            self.dist_path / "data",
            self.dist_path / "logs",
            self.dist_path / "config",
            self.dist_path / "README.txt",
            self.dist_path / ".env.template",
        ]
        
        for file_path in essential_files:
            exists = file_path.exists()
            all_ok = self.print_test(
                f"Fichier/Dossier: {file_path.name}",
                exists,
                "Trouvé" if exists else "Manquant"
            ) and all_ok
        
        return all_ok
    
    def test_exe_launches(self):
        """Test 2: Vérifier que l'exe se lance"""
        self.print_header("TEST 2: Lancement de l'Application")
        
        try:
            # Lancer l'exe
            print(f"  Lancement de {self.exe_path.name}...")
            # Pas de PIPE ici : personne ne lit les sorties, le tampon se remplit
            # avec les logs et le serveur finit par se bloquer (timeouts)
            self.process = subprocess.Popen(
                [str(self.exe_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(self.dist_path)
            )
            
            # Attendre un peu que le serveur démarre
            time.sleep(5)
            
            # Vérifier que le processus tourne
            if self.process.poll() is None:
                return self.print_test(
                    "Processus actif",
                    True,
                    f"PID: {self.process.pid}"
                )
            else:
                return self.print_test(
                    "Processus actif",
                    False,
                    "Le processus s'est arrêté immédiatement"
                )
        
        except Exception as e:
            return self.print_test(
                "Lancement exe",
                False,
                f"Erreur: {str(e)}"
            )
    
    def test_server_responds(self):
        """Test 3: Vérifier que le serveur web répond"""
        self.print_header("TEST 3: Serveur Web")
        
        max_retries = 10
        
        for i in range(max_retries):
            try:
                # Essayer de se connecter au serveur
                response = requests.get(self.base_url, timeout=2)
                
                if response.status_code == 200:
                    return self.print_test(
                        "Serveur répond",
                        True,
                        f"Status: {response.status_code}"
                    )
            
            except requests.exceptions.ConnectionError:
                if i < max_retries - 1:
                    print(f"  Tentative {i+1}/{max_retries}... attente...")
                    time.sleep(2)
                else:
                    return self.print_test(
                        "Serveur répond",
                        False,
                        "Timeout - serveur inaccessible"
                    )
            
            except Exception as e:
                return self.print_test(
                    "Serveur répond",
                    False,
                    f"Erreur: {str(e)}"
                )
        
        return False
    
    def test_endpoints(self):
        """Test 4: Vérifier les endpoints principaux"""
        self.print_header("TEST 4: Endpoints API")
        
        endpoints = [
            ('/', 'Page principale'),
            ('/settings', 'Page settings'),
            ('/viewer', 'Page viewer'),
            ('/status', 'API status'),
            ('/sessions', 'API sessions'),
        ]
        
        all_ok = True
        
        for endpoint, description in endpoints:
            try:
                url = self.base_url + endpoint
                response = requests.get(url, timeout=5)
                
                passed = response.status_code in [200, 302]  # 302 = redirect
                all_ok = self.print_test(
                    description,
                    passed,
                    f"Status: {response.status_code}"
                ) and all_ok
            
            except Exception as e:
                all_ok = self.print_test(
                    description,
                    False,
                    f"Erreur: {str(e)}"
                ) and all_ok
        
        return all_ok
    
    def test_static_files(self):
        """Test 5: Vérifier que les fichiers static sont servis"""
        self.print_header("TEST 5: Fichiers Static")
        
        static_files = [
            '/static/css/main.css',
            '/static/css/settings.css',
            '/static/js/app.js',
            '/static/js/settings.js',
            '/static/js/csv_viewer.js',
            '/static/js/i18n.js',
        ]
        
        all_ok = True
        
        for file_path in static_files:
            try:
                url = self.base_url + file_path
                response = requests.get(url, timeout=5)
                
                passed = response.status_code == 200
                all_ok = self.print_test(
                    f"Static: {file_path}",
                    passed,
                    f"Status: {response.status_code}"
                ) and all_ok
            
            except Exception as e:
                all_ok = self.print_test(
                    f"Static: {file_path}",
                    False,
                    f"Erreur: {str(e)}"
                ) and all_ok
        
        return all_ok
    
    def test_data_directory(self):
        """Test 6: Vérifier que le dossier data est accessible"""
        self.print_header("TEST 6: Dossiers de Données")
        
        directories = [
            ('data', 'Sessions CSV'),
            ('logs', 'Logs application'),
            ('config', 'Configuration'),
            ('recordings', 'Enregistrements'),
        ]
        
        all_ok = True
        
        for dir_name, description in directories:
            dir_path = self.dist_path / dir_name
            
            # Vérifier existence
            exists = dir_path.exists() and dir_path.is_dir()
            
            # Vérifier permissions d'écriture
            writable = False
            if exists:
                try:
                    test_file = dir_path / ".test_write"
                    test_file.touch()
                    test_file.unlink()
                    writable = True
                except:
                    pass
            
            status = "OK (écriture possible)" if writable else ("Existe" if exists else "Manquant")
            passed = exists
            
            all_ok = self.print_test(
                f"{description} ({dir_name}/)",
                passed,
                status
            ) and all_ok
        
        return all_ok
    
    def cleanup(self):
        """Nettoie le processus de test"""
        print("\n" + "="*60)
        print(" NETTOYAGE")
        print("="*60 + "\n")
        
        if self.process and self.process.poll() is None:
            print("  Arrêt du serveur de test...")
            # /T pour arrêter aussi le processus worker, sinon il reste en mémoire
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            try:
                self.process.wait(timeout=5)
                print("  ✓ Serveur arrêté proprement")
            except subprocess.TimeoutExpired:
                print("  ⚠ Forçage de l'arrêt...")
                self.process.kill()
                print("  ✓ Serveur arrêté (forcé)")
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("\n" + "="*60)
        print(" NEUROSITY MONITOR - TESTS AUTOMATIQUES")
        print("="*60)
        print(f"\nDossier de test: {self.dist_path}")
        print(f"Executable: {self.exe_path}")
        
        try:
            # Tests
            results = []
            
            # Test 1: Fichiers
            results.append(("Fichiers et structure", self.test_files_exist()))
            
            # Test 2: Lancement exe
            results.append(("Lancement application", self.test_exe_launches()))
            
            # Si l'exe a démarré, tester le serveur
            if results[-1][1]:
                # Test 3: Serveur répond
                results.append(("Serveur web", self.test_server_responds()))
                
                # Si le serveur répond, tester les endpoints
                if results[-1][1]:
                    # Test 4: Endpoints
                    results.append(("Endpoints API", self.test_endpoints()))
                    
                    # Test 5: Static files
                    results.append(("Fichiers static", self.test_static_files()))
            
            # Test 6: Dossiers (peut se faire indépendamment)
            results.append(("Dossiers données", self.test_data_directory()))
            
            # Résumé
            self.print_header("RÉSUMÉ DES TESTS")
            
            passed_count = sum(1 for _, passed in results if passed)
            total_count = len(results)
            
            for test_name, passed in results:
                symbol = "✓" if passed else "✗"
                status = "PASS" if passed else "FAIL"
                print(f"  {symbol} {test_name}: {status}")
            
            print(f"\nRésultat: {passed_count}/{total_count} tests réussis")
            
            # Conclusion
            print("\n" + "="*60)
            if passed_count == total_count:
                print(" ✓ TOUS LES TESTS ONT RÉUSSI")
                print("="*60 + "\n")
                print("L'application est prête à être distribuée!")
                return True
            else:
                print(" ✗ CERTAINS TESTS ONT ÉCHOUÉ")
                print("="*60 + "\n")
                print("Corrigez les problèmes avant de distribuer.")
                return False
        
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            self.cleanup()


def find_latest_build():
    """Retourne le dossier du build le plus récent dans dist/ (None si aucun)"""
    builds = [p for p in Path("dist").glob("*NeurosityMonitor") if p.is_dir()]
    if not builds:
        return None
    return max(builds, key=lambda p: p.stat().st_mtime)


def main():
    """Fonction principale"""
    # Dossier à tester : passé en argument, sinon le dernier build de dist/
    dist_path = Path(sys.argv[1]) if len(sys.argv) > 1 else find_latest_build()

    if dist_path is None or not dist_path.exists():
        print("\n❌ ERREUR: Aucun build trouvé dans dist/")
        print("\nVous devez d'abord compiler l'application:")
        print("  python organize_project.py")
        print("  build.bat")
        print()
        return False

    # Créer et exécuter les tests
    tester = TestRunner(dist_path)
    success = tester.run_all_tests()
    
    return success


if __name__ == "__main__":
    success = main()
    
    print("\nAppuyez sur Entrée pour fermer...")
    input()
    
    sys.exit(0 if success else 1)
