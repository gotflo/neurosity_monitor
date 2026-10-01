# 🧠 Neurosity Crown Monitor

Une application web moderne de monitoring en temps réel pour le casque EEG Neurosity Crown, avec interface élégante et gestion avancée des données.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Flask](https://img.shields.io/badge/flask-2.3.3-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Table des Matières

- [✨ Fonctionnalités](#-fonctionnalités)
- [🏗️ Architecture](#️-architecture)
- [🚀 Installation](#-installation)
- [⚡ Démarrage Rapide](#-démarrage-rapide)
- [🎯 Utilisation](#-utilisation)
- [⚙️ Configuration](#️-configuration)
- [🌐 Langues (FR / EN)](#-langues-fr--en)
- [📊 Données Collectées](#-données-collectées)
- [🛠️ Technologies](#️-technologies)
- [📁 Structure du Projet](#-structure-du-projet)
- [🐛 Dépannage](#-dépannage)
- [🤝 Contribution](#-contribution)


## ✨ Fonctionnalités

### 🎨 **Interface Moderne**
- **Design soft et moderne** avec palette de couleurs douce
- **Fond blanc** avec gradients subtils et ombres légères
- **Typographie Inter** pour une lisibilité optimale
- **Animations fluides** et transitions CSS
- **Responsive design** compatible mobile et desktop

### 📊 **Monitoring Temps Réel**
- **Métriques principales** : Calme, Concentration, Attention (cercles de progression)
- **Ondes cérébrales** : Delta, Theta, Alpha, Beta, Gamma (graphiques temps réel)
- **WebSocket** pour des mises à jour instantanées
- **Limitation intelligente** à 50 points pour optimiser les performances

### 💾 **Gestion des Données**
- **Enregistrement CSV** avec délimiteur `;` personnalisable
- **Statistiques avancées** : moyenne, min, max, écart-type pour chaque onde
- **Timestamps précis** sur toutes les données
- **Sessions nommées** automatiquement avec date/heure
- **Gestionnaire de fichiers** intégré pour télécharger les sessions

### 🔔 **Système de Notifications**
- **Notifications Toast** modernes et élégantes
- **4 types** : Info (bleu), Succès (vert), Warning (orange), Erreur (rouge)
- **Feedback visuel** pour chaque action utilisateur
- **Auto-suppression** et fermeture manuelle

### 🔗 **Connectivité Neurosity**
- **Connexion automatique** avec identifiants stockés dans `.env`
- **Gestion d'erreurs** robuste avec messages explicites
- **État de connexion** visible en temps réel
- **Monitoring automatique** dès la connexion réussie

## 🏗️ Architecture

### **Frontend**
- **Single Page Application** (SPA) avec interface modulaire
- **Chart.js** pour les graphiques interactifs
- **Socket.IO** pour la communication temps réel
- **CSS moderne** avec variables et animations

### **Backend**
- **Flask** avec extension SocketIO pour WebSocket
- **Neurosity SDK** pour la communication avec le casque
- **Gestionnaire de données** avancé avec export CSV
- **API REST** pour les actions utilisateur

### **Données**
- **CSV structuré** avec délimiteur `;`
- **Statistiques complètes** calculées en temps réel
- **Stockage local** dans le dossier `data/`
- **Sessions horodatées** automatiquement

## 🚀 Installation

### Prérequis
- **Python 3.8+** installé sur votre système
- **Casque Neurosity Crown** configuré
- **Compte développeur Neurosity** avec API access

### 1. Cloner le Projet
```bash
git clone https://github.com/votre-username/neurosity-monitor.git
cd neurosity-monitor
```

### 2. Installation Automatique (Recommandé)
```bash
python install.py
```
Le script d'installation va :
- ✅ Créer l'environnement virtuel
- ✅ Installer toutes les dépendances
- ✅ Créer la structure de dossiers
- ✅ Configurer le fichier `.env` de manière interactive

### 3. Installation Manuelle
```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows :
venv\Scripts\activate
# Linux/macOS :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Créer les dossiers nécessaires
mkdir data logs
```

## ⚡ Démarrage Rapide

### 1. Configuration
Créez un fichier `.env` à la racine avec vos identifiants Neurosity :

```env
# Identifiants Neurosity (REQUIS)
NEUROSITY_EMAIL=votre_email@exemple.com
NEUROSITY_PASSWORD=votre_mot_de_passe
NEUROSITY_DEVICE_ID=votre_device_id

# Configuration Flask (optionnel)
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### 2. Lancement
```bash
# Méthode recommandée
python run.py

# Ou directement
python app.py

# Ou avec les scripts de lancement
./start.sh    # Linux/macOS
start.bat     # Windows
```

### 3. Accès à l'Application
Ouvrez votre navigateur sur : **http://localhost:5000**

## 🎯 Utilisation

### 📋 **Workflow Standard**

1. **🚀 Démarrage de l'Application**
   - Lancez `python run.py`
   - Ouvrez http://localhost:5000
   - L'interface se charge avec graphiques vides (normal)

2. **🧠 Préparation du Casque**
   - Allumez votre Neurosity Crown
   - Assurez-vous qu'il est connecté à votre réseau WiFi
   - Vérifiez que les électrodes sont bien positionnées

3. **🔗 Connexion**
   - Cliquez sur le bouton **"Connecter"** (bleu)
   - L'application utilise automatiquement vos identifiants `.env`
   - Attendez la notification de succès ✅

4. **📊 Monitoring**
   - Les graphiques commencent à afficher des données en temps réel
   - Les cercles de métriques se mettent à jour automatiquement
   - Observez vos ondes cérébrales en direct !

5. **⏺️ Enregistrement (Optionnel)**
   - Cliquez **"Enregistrer"** pour sauvegarder vos données
   - Le fichier CSV est créé automatiquement dans `data/`
   - Cliquez **"Arrêter"** pour terminer l'enregistrement

6. **💾 Téléchargement**
   - Utilisez **"Télécharger CSV"** pour obtenir la dernière session
   - Ou parcourez les **"Sessions Enregistrées"** pour des fichiers spécifiques

### 🎛️ **Interface Utilisateur**

#### **Barre de Navigation**
- **🔗 Connecter** : Établit la connexion avec votre casque
- **⏺️ Enregistrer** : Démarre/arrête la sauvegarde en CSV
- **⬇️ Télécharger CSV** : Télécharge la session la plus récente
- **🔴 État** : Indicateur visuel de connexion et d'enregistrement

#### **Métriques Principales**
- **🧘 Calme** : Niveau de relaxation (0-100%)
- **🎯 Concentration** : Niveau de focus (0-100%)
- **⚡ Attention** : Niveau d'attention (0-100%)

#### **Graphique Temps Réel**
- **📈 5 Ondes** : Delta, Theta, Alpha, Beta, Gamma
- **⏱️ Historique** : 50 derniers points (optimisation performance)
- **🕐 Timestamps** : Mise à jour en temps réel

#### **Gestion des Sessions**
- **📁 Liste** : Toutes vos sessions enregistrées
- **📊 Téléchargement** : Un clic pour obtenir le CSV
- **🔄 Actualisation** : Mise à jour de la liste

## ⚙️ Configuration

### **Variables d'Environnement (.env)**

| Variable | Description | Requis | Défaut |
|----------|-------------|---------|---------|
| `NEUROSITY_EMAIL` | Email de votre compte Neurosity | ✅ | - |
| `NEUROSITY_PASSWORD` | Mot de passe Neurosity | ✅ | - |
| `NEUROSITY_DEVICE_ID` | ID de votre casque Crown | ✅ | - |
| `FLASK_HOST` | Adresse d'écoute du serveur | ❌ | `0.0.0.0` |
| `FLASK_PORT` | Port du serveur | ❌ | `5000` |
| `FLASK_DEBUG` | Mode debug Flask | ❌ | `True` |
| `CSV_DELIMITER` | Séparateur CSV | ❌ | `;` |
| `MAX_CHART_POINTS` | Points max sur graphique | ❌ | `50` |

### **Obtenir vos Identifiants Neurosity**

1. **Compte Développeur** : Créez un compte sur [console.neurosity.co](https://console.neurosity.co)
2. **Device ID** : Trouvez l'ID dans l'app mobile Neurosity ou la console web
3. **API Access** : Assurez-vous d'avoir accès à l'API développeur

## 🌐 Langues (FR / EN)

Toute la plateforme est bilingue : **français par défaut**, anglais au choix
de l'utilisateur. Le basculement est instantané, sans rechargement, et couvre
l'intégralité de l'interface — y compris les **graphiques** (titres, légendes,
axes, infobulles), les notifications, les boîtes de confirmation, les messages
d'erreur du serveur, ainsi que les formats de date, d'heure et de nombre.

### Où changer de langue

| Page | Emplacement du sélecteur |
|------|--------------------------|
| Tableau de bord | Barre de navigation, bouton `FR` / `EN` |
| Configuration | Section « Paramètres optionnels » → « Langue de l'interface » |
| Visualisation CSV | En-tête, à droite du titre |

Le choix est mémorisé dans le `localStorage`, dans un cookie `neuro_lang`
(lu par Flask pour rendre `<html lang>` dès le premier affichage) et dans la
configuration chiffrée de l'utilisateur via `POST /api/language`.

### Architecture

| Fichier | Rôle |
|---------|------|
| `static/js/i18n.js` | Moteur côté client : dictionnaires FR/EN, `t()`, sélecteur, formats localisés |
| `static/css/i18n.css` | Styles du sélecteur de langue |
| `i18n.py` | Messages côté serveur (réponses d'API, console) + `lang`/`t` dans Jinja |

Les réponses d'API renvoient un **code stable** (`{'error': ..., 'code': 'device_not_detected'}`)
en plus du texte : le client traduit lui-même le message, quelle que soit la
langue du serveur.

### Traduire le HTML

```html
<span data-i18n="metric.calm">Calme</span>                    <!-- textContent -->
<div  data-i18n-html="replay.hint">...</div>                  <!-- innerHTML -->
<input data-i18n-attr="placeholder:settings.email.placeholder"><!-- attributs -->
<div data-i18n-switcher></div>                                <!-- sélecteur FR/EN -->
```

Le texte écrit dans le HTML sert de repli français : il est remplacé au
chargement par la valeur du dictionnaire.

### Traduire le JavaScript

```js
t('toast.connected')                        // chaîne simple
t('toast.downloading', { file: nom })       // interpolation {file}
I18n.plural('sessions.count', n)            // .zero / .one / .other
I18n.formatTime(ts)                         // heure selon la locale
I18n.fromServer(reponse, 'toast.unknownError') // message d'API via son code
I18n.onChange(() => { /* re-rendu dynamique */ })
```

Tout contenu généré en JavaScript (liste des sessions, boutons d'état,
graphiques) est re-rendu via un callback `I18n.onChange`.

### Ajouter une langue

1. Ajouter le code (ex. `'es'`) à `SUPPORTED` et un dictionnaire dans
   `static/js/i18n.js`, plus une entrée dans `LOCALES` (ex. `'es-ES'`).
2. Ajouter la même langue à `SUPPORTED_LANGS` et à `TRANSLATIONS` dans `i18n.py`.
3. Le sélecteur FR/EN se construit à partir de `SUPPORTED` : aucun HTML à modifier.

Une clé absente d'une langue retombe automatiquement sur le français, avec un
avertissement dans la console du navigateur.

## 📊 Données Collectées

### **Format CSV (Délimiteur `;`)**

Une session produit **68 colonnes**. Les 8 électrodes du Crown sont, dans
l'ordre : `CP3, C3, F5, PO3, PO4, F6, C4, CP4`.

| Colonne | Description | Format |
|---------|-------------|---------|
| `timestamp` | Horodatage ISO | `2025-06-09T14:30:15.123456` |
| `session_duration` | Durée depuis le début de la session | `125.45` (secondes) |
| `calm_probability` | Probabilité de calme | `0.75` (0-1) |
| `focus_probability` | Probabilité de concentration | `0.68` (0-1) |
| `delta_<électrode>` | Puissance Delta, **une colonne par électrode** (8) | `0.245` (µV²) |
| `theta_<électrode>` | Idem pour Theta (8) | `0.312` (µV²) |
| `alpha_<électrode>` | Idem pour Alpha (8) | `1.874` (µV²) |
| `beta_<électrode>` | Idem pour Beta (8) | `0.593` (µV²) |
| `gamma_<électrode>` | Idem pour Gamma (8) | `0.104` (µV²) |
| `eeg_<électrode>` | Signal brut moyenné sur le paquet reçu (8) | `-12.482` (µV) |
| `signal_status_<électrode>` | Qualité du contact électrode-peau (8) | `great` \| `good` \| `bad` \| `noContact` |
| `signal_std_<électrode>` | Écart-type du signal servant à évaluer la qualité (8) | `1.732` |

Exemple de noms complets : `delta_CP3`, `eeg_PO4`, `signal_status_F5`, `signal_std_C4`.

### **Qualité du signal (`signalQuality`)**

Reprend le type du SDK Neurosity
([`signalQuality.ts`](https://github.com/neurosity/neurosity-sdk-js/blob/main/src/types/signalQuality.ts)) :
chaque canal expose un `status` et un `standardDeviation`.

| Statut | Signification |
|--------|---------------|
| `great` | Contact excellent, signal exploitable |
| `good` | Contact correct |
| `bad` | Contact dégradé, données à interpréter avec prudence |
| `noContact` | Électrode non en contact, données non exploitables |

Ces colonnes permettent d'**écarter a posteriori les segments enregistrés avec un
mauvais contact**, ce qui était impossible auparavant : la qualité n'était
affichée qu'en temps réel sur le tableau de bord.

Comportement d'écriture : la qualité du signal est une **métadonnée
d'acquisition**. Elle met à jour un buffer mais ne crée pas de ligne à elle
seule ; la dernière valeur connue est jointe à la prochaine ligne produite par
les flux calm / focus / brainwaves / EEG brut. La cadence des lignes reste donc
identique aux sessions précédentes. Une électrode dont aucune mesure n'est
encore arrivée laisse la cellule vide.

`analyze_session()` (route `/analyze/<fichier>`) renvoie en plus, par électrode :
la répartition des statuts, le statut dominant, le pourcentage de temps
exploitable (`great` + `good`) et les statistiques d'écart-type.

> **Compatibilité** : les sessions enregistrées avant l'ajout de ces colonnes
> restent lisibles et analysables, sans colonne `signal_*`.

### **Fréquences des Ondes Cérébrales**

- **🔵 Delta (1-4 Hz)** : Sommeil profond, récupération
- **🟣 Theta (4-8 Hz)** : Créativité, méditation profonde
- **🟢 Alpha (8-13 Hz)** : Relaxation éveillée, flow
- **🟡 Beta (13-30 Hz)** : Concentration active, résolution de problèmes
- **🔴 Gamma (30-100 Hz)** : Traitement cognitif élevé, insights

## 🛠️ Technologies

### **Backend**
- **Flask 2.3.3** - Framework web Python
- **Flask-SocketIO 5.3.6** - WebSocket temps réel
- **Neurosity SDK 2.1.1** - Interface casque EEG
- **python-dotenv 1.0.0** - Gestion variables d'environnement
- **pandas 2.1.0** - Manipulation données CSV

### **Frontend**
- **Chart.js 3.9.1** - Graphiques interactifs
- **Socket.IO 4.7.2** - Client WebSocket
- **Vanilla JavaScript** - Logique métier
- **CSS3 moderne** - Animations et responsive

### **Fonts & Design**
- **Inter Font** - Typographie moderne Google Fonts
- **Design System** - Variables CSS et composants modulaires
- **Glassmorphism** - Effets de transparence et blur

## 📁 Structure du Projet

```
neurosity-monitor/
├── 📄 **Backend**
│   ├── app.py                          # Application Flask principale
│   ├── data_manager.py                 # Gestionnaire de données CSV
│   ├── run.py                         # Script de lancement avec vérifications
│   └── requirements.txt               # Dépendances Python
│
├── 📄 **Configuration**
│   ├── .env                           # Identifiants Neurosity (à créer)
│   ├── .gitignore                     # Fichiers ignorés par Git
│   └── config/
│       └── settings.py                # Configuration centralisée
│
├── 📁 **Frontend**
│   ├── templates/
│   │   ├── base.html                  # Template de base HTML
│   │   ├── index.html                 # Page principale
│   │   └── components/                # Composants réutilisables
│   │       ├── navbar.html            # Barre de navigation
│   │       ├── metrics.html           # Cercles de métriques
│   │       └── charts.html            # Container graphiques
│   └── static/
│       ├── css/
│       │   ├── main.css              # Styles principaux et layout
│       │   ├── components.css        # Styles composants UI
│       │   └── animations.css        # Animations et transitions
│       └── js/
│           └── app.js                # Application JavaScript unifiée
│
├── 📁 **Utilitaires**
│   ├── utils/
│   │   └── neurosity_helper.py       # Helpers SDK Neurosity
│   ├── install.py                    # Installation automatique
│   ├── quick_fix.py                  # Correction problèmes .env
│   └── start.sh / start.bat          # Scripts de lancement
│
├── 📁 **Données (Générées)**
│   ├── data/                         # Sessions CSV sauvegardées
│   ├── logs/                         # Logs de l'application
│   └── venv/                         # Environnement virtuel Python
│
├── 📁 **Documentation**
│   ├── README.md                     # Ce fichier
│   ├── DEPLOYMENT.md                 # Guide de déploiement
│   └── docs/                         # Documentation technique
│
└── 📁 **Déploiement (Optionnel)**
    ├── Dockerfile                    # Configuration Docker
    ├── docker-compose.yml            # Orchestration multi-services
    └── nginx.conf                    # Configuration Nginx
```

## 🐛 Dépannage

### **❌ Problèmes Courants**

#### **1. Erreur d'Encodage `.env`**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte
```
**Solution :**
```bash
python quick_fix.py
```
Ou éditez manuellement votre `.env` en supprimant les accents.

#### **2. Casque Non Connecté**
```
Erreur de connexion au casque
```
**Vérifications :**
- ✅ Casque allumé et chargé
- ✅ WiFi connecté
- ✅ Identifiants corrects dans `.env`
- ✅ Électrodes bien positionnées

#### **3. Graphiques Vides**
**Normal si :**
- ❌ Casque pas encore connecté
- ❌ Première utilisation

**Problème si :**
- ✅ Casque connecté mais pas de données après 30 secondes

#### **4. Port 5000 Occupé**
```
Address already in use
```
**Solution :**
```bash
# Changer le port dans .env
FLASK_PORT=5001

# Ou tuer le processus existant
# Windows :
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS :
lsof -ti:5000 | xargs kill -9
```

### **🔍 Diagnostic**

#### **Logs Serveur**
```bash
# Lancer avec logs détaillés
python run.py
```

#### **Console Navigateur**
```javascript
// Ouvrir F12 > Console
console.log(window.AppState)  // État de l'application
debugCharts()                 // Diagnostic graphiques (mode debug)
```

#### **Test de Connexion**
```python
# Test manuel de connexion
python -c "
from neurosity import NeurositySDK
import os
from dotenv import load_dotenv

load_dotenv()
sdk = NeurositySDK({'device_id': os.getenv('NEUROSITY_DEVICE_ID')})
print('Test connexion...')
result = sdk.login({'email': os.getenv('NEUROSITY_EMAIL'), 'password': os.getenv('NEUROSITY_PASSWORD')})
print('Succès !' if result else 'Échec')
"
```

### **🆘 Support d'Urgence**

1. **Navigation Privée** : Testez dans un onglet privé
2. **Cache Navigateur** : Ctrl+F5 pour vider le cache
3. **Restart Complet** : Arrêt serveur + redémarrage + actualisation
4. **Réinstallation** : Supprimez `venv/` et relancez `python install.py`

## 🚀 Performance

### **Optimisations Intégrées**
- **Limitation graphiques** : 50 points maximum pour fluidité
- **Animations GPU** : Accélération matérielle CSS
- **WebSocket efficace** : Mise à jour uniquement si nouvelles données
- **Debouncing** : Éviter les appels API excessifs

### **Recommandations d'Usage**
- **RAM** : 4GB minimum recommandés
- **Navigateur** : Chrome/Firefox récents pour meilleures performances
- **Réseau** : WiFi stable pour casque + ordinateur
- **Sessions** : Limiter à 2-3h continues pour éviter fichiers trop volumineux

## 🤝 Contribution

### **Développement Local**
```bash
# Fork le repo et cloner
git clone 
cd neurosity_monitor

# Créer une branche feature
git checkout -b feature/nouvelle-fonctionnalite

# Développer et tester
python run.py

# Commit et push
git add .
git commit -m "feat: ajouter nouvelle fonctionnalité"
git push origin feature/nouvelle-fonctionnalite
```

### **Guidelines**
- ✅ **Code clean** : Suivre les conventions Python PEP8
- ✅ **Documentation** : Commenter les fonctions importantes
- ✅ **Tests** : Tester manuellement avant soumission
- ✅ **Responsive** : Vérifier compatibilité mobile
- ✅ **Performance** : Optimiser pour fluidité temps réel

### **Fonctionnalités Souhaitées**
- 🎨 **Thèmes** : Mode sombre, thèmes colorés
- 📊 **Nouveaux graphiques** : Spectrogrammes, heatmaps
- 🔔 **Alertes** : Notifications push, seuils personnalisables
- 📱 **Mobile** : App companion React Native
- 🤖 **IA** : Prédictions, insights automatiques



### **Ressources**
- **📖 Documentation Neurosity** : [docs.neurosity.co](https://docs.neurosity.co)
- **💬 Community** : [Discord Neurosity](https://discord.gg/neurosity)




