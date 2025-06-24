#!/usr/bin/env python3
"""
Test spécifique pour brainwaves_power_by_band
"""

import os
import time
import json
from dotenv import load_dotenv
from neurosity import NeurositySDK

load_dotenv()


def test_power_by_band():
    """Test de la méthode brainwaves_power_by_band"""
    
    print("🧠 TEST DE BRAINWAVES_POWER_BY_BAND")
    print("=" * 50)
    
    try:
        # Initialiser et connecter
        neurosity = NeurositySDK({
            "device_id": os.getenv("NEUROSITY_DEVICE_ID")
        })
        
        neurosity.login({
            "email": os.getenv("NEUROSITY_EMAIL"),
            "password": os.getenv("NEUROSITY_PASSWORD")
        })
        
        print("✅ Connecté avec succès!")
        
        # Collecter des données
        data_samples = []
        
        def callback(data):
            """Capture les données power_by_band"""
            data_samples.append(data)
            
            print(f"\n📊 Échantillon #{len(data_samples)}:")
            print(f"  Type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"  Clés principales: {list(data.keys())}")
                
                # Explorer la structure
                for key, value in data.items():
                    if key in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                        if isinstance(value, (int, float)):
                            print(f"  {key}: {value:.3f}")
                        elif isinstance(value, list):
                            print(f"  {key}: [liste de {len(value)} valeurs]")
                            if len(value) > 0:
                                print(f"    Moyenne: {sum(value) / len(value):.3f}")
                                print(f"    Min: {min(value):.3f}, Max: {max(value):.3f}")
                    elif key == 'data':
                        if isinstance(value, dict):
                            print(f"  data: {list(value.keys())}")
                            # Vérifier si les bandes sont dans 'data'
                            for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
                                if band in value:
                                    band_value = value[band]
                                    if isinstance(band_value, (int, float)):
                                        print(f"    data.{band}: {band_value:.3f}")
                                    elif isinstance(band_value, list) and len(band_value) > 0:
                                        print(f"    data.{band}: moyenne={sum(band_value) / len(band_value):.3f}")
                    elif key == 'powerByBand':
                        if isinstance(value, dict):
                            print(f"  powerByBand:")
                            for band, power in value.items():
                                if isinstance(power, (int, float)):
                                    print(f"    {band}: {power:.3f}")
                                elif isinstance(power, list) and len(power) > 0:
                                    print(f"    {band}: moyenne={sum(power) / len(power):.3f}")
        
        # Test 1: brainwaves_power_by_band
        print("\n🔬 Test de brainwaves_power_by_band...")
        print("-" * 30)
        
        try:
            unsub = neurosity.brainwaves_power_by_band(callback)
            print("⏳ Collecte de données pendant 10 secondes...")
            time.sleep(10)
            unsub()
            
            print(f"\n✅ Test terminé! {len(data_samples)} échantillons collectés")
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        # Analyser les résultats
        if data_samples:
            print("\n📊 ANALYSE DES DONNÉES:")
            print("-" * 30)
            
            # Afficher le premier échantillon complet
            print("\nPremier échantillon complet (JSON):")
            try:
                print(json.dumps(data_samples[0], indent=2))
            except:
                print(f"Impossible de sérialiser en JSON: {data_samples[0]}")
            
            # Déterminer la structure
            first_sample = data_samples[0]
            print("\n🔍 Structure détectée:")
            
            if isinstance(first_sample, dict):
                # Cas 1: Bandes directement dans le dict principal
                if all(band in first_sample for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']):
                    print("✅ Les bandes sont directement dans le dictionnaire principal")
                
                # Cas 2: Bandes dans une sous-clé 'data'
                elif 'data' in first_sample and isinstance(first_sample['data'], dict):
                    if all(band in first_sample['data'] for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']):
                        print("✅ Les bandes sont dans data.{band}")
                
                # Cas 3: Bandes dans 'powerByBand'
                elif 'powerByBand' in first_sample:
                    print("✅ Les bandes sont dans powerByBand.{band}")
                
                # Autre structure
                else:
                    print("❓ Structure non standard, clés disponibles:", list(first_sample.keys()))
        
        # Test 2: Comparer avec brainwaves_psd
        print("\n\n🔬 Test comparatif avec brainwaves_psd...")
        print("-" * 30)
        
        psd_samples = []
        
        def psd_callback(data):
            psd_samples.append(data)
            if len(psd_samples) == 1:
                print(f"\nPremier échantillon PSD:")
                print(f"  Type: {type(data)}")
                print(f"  Clés: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        
        try:
            unsub = neurosity.brainwaves_psd(psd_callback)
            time.sleep(3)
            unsub()
            print(f"✅ {len(psd_samples)} échantillons PSD collectés")
        except Exception as e:
            print(f"❌ Erreur PSD: {e}")
        
        # Déconnexion
        neurosity.logout()
        print("\n✅ Test complet terminé!")
    
    except Exception as e:
        print(f"\n❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_power_by_band()