@echo off
REM ============================================
REM NEUROSITY MONITOR - SCRIPT DE BUILD COMPLET
REM Génère un .exe qui ouvre l'app dans le navigateur
REM ============================================

setlocal enabledelayedexpansion

REM Nom du build : jour_mois_annee_NeurosityMonitor (ex: 01_10_26_NeurosityMonitor)
REM pour distinguer les differents exe generes
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format dd_MM_yy"') do set BUILD_DATE=%%i
set APP_NAME=%BUILD_DATE%_NeurosityMonitor

echo.
echo ============================================
echo  NEUROSITY MONITOR - BUILD AUTOMATIQUE
echo ============================================
echo.
echo Build: %APP_NAME%
echo.

REM ============================================
REM 1. VÉRIFICATIONS PRÉALABLES
REM ============================================

echo [1/10] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans PATH
    echo.
    echo Installez Python depuis: https://www.python.org/downloads/
    echo N'oubliez pas de cocher "Add Python to PATH"
    pause
    exit /b 1
)

python --version
echo.

REM ============================================
REM 2. CRÉATION STRUCTURE DE DOSSIERS
REM ============================================

echo [2/10] Creation de la structure de dossiers...

REM Créer dossiers templates
if not exist "templates" mkdir templates
if not exist "templates\components" mkdir templates\components

REM Créer dossiers static
if not exist "static" mkdir static
if not exist "static\css" mkdir static\css
if not exist "static\js" mkdir static\js
if not exist "static\assets" mkdir static\assets

REM Créer dossiers config
if not exist "config" mkdir config

REM Créer dossiers utils
if not exist "utils" mkdir utils

REM Créer dossiers pour runtime
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "recordings" mkdir recordings

echo   - templates/
echo   - static/css/
echo   - static/js/
echo   - config/
echo   - utils/
echo   - data/
echo   - logs/
echo   - recordings/
echo.

REM ============================================
REM 3. COPIE DES FICHIERS VERS LA BONNE STRUCTURE
REM ============================================

echo [3/10] Organisation des fichiers...

REM Copier les fichiers HTML vers templates/
if exist "index.html" (
    copy /Y "index.html" "templates\index.html" >nul
    echo   - index.html copie vers templates/
)
if exist "settings.html" (
    copy /Y "settings.html" "templates\settings.html" >nul
    echo   - settings.html copie vers templates/
)

REM Copier les fichiers CSS vers static/css/
if exist "main.css" (
    copy /Y "main.css" "static\css\main.css" >nul
    echo   - main.css copie vers static/css/
)
if exist "settings.css" (
    copy /Y "settings.css" "static\css\settings.css" >nul
    echo   - settings.css copie vers static/css/
)

REM Copier les fichiers JS vers static/js/
if exist "app.js" (
    copy /Y "app.js" "static\js\app.js" >nul
    echo   - app.js copie vers static/js/
)
if exist "settings.js" (
    copy /Y "settings.js" "static\js\settings.js" >nul
    echo   - settings.js copie vers static/js/
)

REM Copier config_manager.py et settings.py vers config/
if exist "config_manager.py" (
    copy /Y "config_manager.py" "config\config_manager.py" >nul
    echo   - config_manager.py copie vers config/
)
if exist "settings.py" (
    copy /Y "settings.py" "config\settings.py" >nul
    echo   - settings.py copie vers config/
)

REM Créer __init__.py pour les packages
echo. > "config\__init__.py" 2>nul
echo. > "utils\__init__.py" 2>nul

REM Copier neurosity_helper.py vers utils/
if exist "neurosity_helper.py" (
    copy /Y "neurosity_helper.py" "utils\neurosity_helper.py" >nul
    echo   - neurosity_helper.py copie vers utils/
)

echo.

REM ============================================
REM 4. ENVIRONNEMENT VIRTUEL
REM ============================================

echo [4/10] Configuration environnement virtuel...

if not exist ".venv" (
    echo   Creation de l'environnement virtuel...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERREUR] Impossible de creer l'environnement virtuel
        pause
        exit /b 1
    )
    echo   Environnement virtuel cree avec succes
) else (
    echo   Environnement virtuel existe deja
)

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERREUR] Impossible d'activer l'environnement virtuel
    pause
    exit /b 1
)

echo   Environnement virtuel active
echo.

REM ============================================
REM 5. INSTALLATION DÉPENDANCES
REM ============================================

echo [5/10] Installation des dependances Python...

REM Mettre à jour pip
python -m pip install --upgrade pip --quiet

REM Installer depuis requirements.txt si existe
if exist "requirements.txt" (
    echo   Installation depuis requirements.txt...
    pip install -r requirements.txt --quiet
) else (
    echo   Installation manuelle des packages...
    pip install Flask==3.0.0 --quiet
    pip install Flask-SocketIO==5.3.5 --quiet
    pip install neurosity==2.0.0 --quiet
    pip install cryptography==41.0.7 --quiet
    pip install python-dotenv==1.0.0 --quiet
    pip install pandas==2.1.4 --quiet
    pip install numpy==1.26.2 --quiet
    pip install requests==2.31.0 --quiet
)

REM Installer PyInstaller
echo   Installation de PyInstaller...
pip install pyinstaller==6.3.0 --quiet

echo   Toutes les dependances sont installees
echo.

REM ============================================
REM 6. VÉRIFICATION DU CODE
REM ============================================

echo [6/10] Verification du code Python...

python -c "import app; print('  Code app.py: OK')" 2>nul
if errorlevel 1 (
    echo   [AVERTISSEMENT] Probleme dans app.py
    echo   Compilation continue quand meme...
)

python -c "import data_manager; print('  Code data_manager.py: OK')" 2>nul
python -c "import neurosity_worker; print('  Code neurosity_worker.py: OK')" 2>nul

echo.

REM ============================================
REM 7. NETTOYAGE BUILDS PRÉCÉDENTS
REM ============================================

echo [7/10] Nettoyage des anciens builds...

if exist "build" (
    rmdir /s /q build
    echo   - build/ supprime
)
REM On garde les anciens builds dates, on ne supprime que celui du jour
if exist "dist\%APP_NAME%" (
    rmdir /s /q "dist\%APP_NAME%"
    echo   - dist/%APP_NAME%/ supprime
)
if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo   - __pycache__/ supprime
)
if exist "NeurosityMonitor.spec" (
    del /q NeurosityMonitor.spec
    echo   - NeurosityMonitor.spec supprime
)

REM Nettoyer les __pycache__ dans les sous-dossiers
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo.

REM ============================================
REM 8. COMPILATION PYINSTALLER
REM ============================================

echo [8/10] Compilation avec PyInstaller...
echo.
echo Configuration:
echo   - Mode: One-directory
echo   - Console: Visible (debug)
echo   - Multiprocessing: Spawn mode
echo   - SocketIO: Threading mode
echo.

pyinstaller neurosity_monitor.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERREUR] La compilation a echoue
    echo Verifiez les messages d'erreur ci-dessus
    pause
    exit /b 1
)

echo.

REM ============================================
REM 9. POST-BUILD - ORGANISATION
REM ============================================

echo [9/10] Organisation de la distribution...

set DIST_DIR=dist\%APP_NAME%

REM Créer dossiers runtime dans dist
if not exist "%DIST_DIR%\data" mkdir "%DIST_DIR%\data"
if not exist "%DIST_DIR%\logs" mkdir "%DIST_DIR%\logs"
if not exist "%DIST_DIR%\config" mkdir "%DIST_DIR%\config"
if not exist "%DIST_DIR%\recordings" mkdir "%DIST_DIR%\recordings"

echo   - Dossiers runtime crees

REM Vérifier et copier templates/static si dans _internal
if exist "%DIST_DIR%\_internal\templates" (
    if not exist "%DIST_DIR%\templates" (
        xcopy "%DIST_DIR%\_internal\templates" "%DIST_DIR%\templates\" /E /I /Y >nul
        echo   - templates/ copie depuis _internal
    )
)

if exist "%DIST_DIR%\_internal\static" (
    if not exist "%DIST_DIR%\static" (
        xcopy "%DIST_DIR%\_internal\static" "%DIST_DIR%\static\" /E /I /Y >nul
        echo   - static/ copie depuis _internal
    )
)

REM Créer fichier .env.template
echo # ============================================ > "%DIST_DIR%\.env.template"
echo # NEUROSITY MONITOR - CONFIGURATION >> "%DIST_DIR%\.env.template"
echo # ============================================ >> "%DIST_DIR%\.env.template"
echo # >> "%DIST_DIR%\.env.template"
echo # IMPORTANT: Renommez ce fichier en .env >> "%DIST_DIR%\.env.template"
echo # et remplissez vos informations >> "%DIST_DIR%\.env.template"
echo # >> "%DIST_DIR%\.env.template"
echo # OU utilisez l'interface Settings dans l'application >> "%DIST_DIR%\.env.template"
echo # (recommande - configuration chiffree) >> "%DIST_DIR%\.env.template"
echo # ============================================ >> "%DIST_DIR%\.env.template"
echo. >> "%DIST_DIR%\.env.template"
echo NEUROSITY_EMAIL=votre.email@example.com >> "%DIST_DIR%\.env.template"
echo NEUROSITY_PASSWORD=votre_mot_de_passe >> "%DIST_DIR%\.env.template"
echo NEUROSITY_DEVICE_ID=votre_device_id >> "%DIST_DIR%\.env.template"
echo. >> "%DIST_DIR%\.env.template"
echo FLASK_HOST=0.0.0.0 >> "%DIST_DIR%\.env.template"
echo FLASK_PORT=5000 >> "%DIST_DIR%\.env.template"

echo   - .env.template cree

REM Créer README complet
echo ============================================ > "%DIST_DIR%\README.txt"
echo NEUROSITY MONITOR - APPLICATION COMPILEE >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo VERSION: 1.0.0 >> "%DIST_DIR%\README.txt"
echo BUILD DATE: %DATE% %TIME% >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo DEMARRAGE RAPIDE >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo 1. ALLUMEZ votre casque Neurosity Crown >> "%DIST_DIR%\README.txt"
echo 2. PORTEZ-LE correctement sur votre tete >> "%DIST_DIR%\README.txt"
echo 3. DOUBLE-CLIQUEZ sur %APP_NAME%.exe >> "%DIST_DIR%\README.txt"
echo 4. Le navigateur s'ouvre automatiquement >> "%DIST_DIR%\README.txt"
echo 5. Cliquez sur "Settings" en haut a droite >> "%DIST_DIR%\README.txt"
echo 6. Entrez vos identifiants Neurosity >> "%DIST_DIR%\README.txt"
echo 7. Cliquez "Connecter" puis "Enregistrer" >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo STRUCTURE DES DOSSIERS >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo %APP_NAME%.exe  - Executable principal >> "%DIST_DIR%\README.txt"
echo _internal\            - Dependances (NE PAS MODIFIER) >> "%DIST_DIR%\README.txt"
echo data\                 - Sessions EEG enregistrees (CSV) >> "%DIST_DIR%\README.txt"
echo logs\                 - Fichiers de logs >> "%DIST_DIR%\README.txt"
echo config\               - Configuration chiffree >> "%DIST_DIR%\README.txt"
echo recordings\           - Enregistrements supplementaires >> "%DIST_DIR%\README.txt"
echo .env.template         - Template de configuration >> "%DIST_DIR%\README.txt"
echo README.txt            - Ce fichier >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo CONFIGURATION >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo METHODE 1 (RECOMMANDEE): >> "%DIST_DIR%\README.txt"
echo   - Utilisez l'interface Settings dans l'application >> "%DIST_DIR%\README.txt"
echo   - Les credentials sont stockes de maniere chiffree >> "%DIST_DIR%\README.txt"
echo   - Plus securise et plus simple >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo METHODE 2 (ALTERNATIVE): >> "%DIST_DIR%\README.txt"
echo   - Renommez .env.template en .env >> "%DIST_DIR%\README.txt"
echo   - Editez le fichier .env >> "%DIST_DIR%\README.txt"
echo   - Remplissez vos identifiants Neurosity >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo DONNEES ENREGISTREES >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo Les sessions sont enregistrees en CSV dans data\ >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo Format: neurosity_session_YYYYMMDD_HHMMSS.csv >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo Colonnes: >> "%DIST_DIR%\README.txt"
echo   - timestamp, session_duration >> "%DIST_DIR%\README.txt"
echo   - calm_probability, focus_probability >> "%DIST_DIR%\README.txt"
echo   - delta, theta, alpha, beta, gamma (8 electrodes) >> "%DIST_DIR%\README.txt"
echo   - eeg brut (8 electrodes) >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo Electrodes: CP3, C3, F5, PO3, PO4, F6, C4, CP4 >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo RESOLUTION DE PROBLEMES >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo L'executable ne demarre pas: >> "%DIST_DIR%\README.txt"
echo   - Verifiez votre antivirus >> "%DIST_DIR%\README.txt"
echo   - Executez en tant qu'administrateur >> "%DIST_DIR%\README.txt"
echo   - Consultez les logs dans logs\ >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo Connexion au casque echoue: >> "%DIST_DIR%\README.txt"
echo   - Verifiez que le casque est allume >> "%DIST_DIR%\README.txt"
echo   - Verifiez que le casque est porte >> "%DIST_DIR%\README.txt"
echo   - Verifiez vos identifiants >> "%DIST_DIR%\README.txt"
echo   - Verifiez votre connexion Internet >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo Port 5000 deja utilise: >> "%DIST_DIR%\README.txt"
echo   - L'application trouvera automatiquement >> "%DIST_DIR%\README.txt"
echo     un port libre (5001, 5002, etc.) >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo Le navigateur ne s'ouvre pas: >> "%DIST_DIR%\README.txt"
echo   - Ouvrez manuellement: http://localhost:5000 >> "%DIST_DIR%\README.txt"
echo   - Ou le port indique dans la console >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo RACCOURCIS CLAVIER >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo Ctrl+K : Connecter/Deconnecter >> "%DIST_DIR%\README.txt"
echo Ctrl+R : Demarrer/Arreter enregistrement >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo SUPPORT >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo Documentation Neurosity: https://docs.neurosity.co >> "%DIST_DIR%\README.txt"
echo Support Neurosity: support@neurosity.co >> "%DIST_DIR%\README.txt"
echo. >> "%DIST_DIR%\README.txt"
echo ============================================ >> "%DIST_DIR%\README.txt"

echo   - README.txt cree
echo.

REM ============================================
REM 10. VÉRIFICATION FINALE
REM ============================================

echo [10/10] Verification finale...

if exist "%DIST_DIR%\%APP_NAME%.exe" (
    echo   - %APP_NAME%.exe: OK
) else (
    echo   [ERREUR] Executable non trouve
    pause
    exit /b 1
)

if exist "%DIST_DIR%\_internal" (
    echo   - _internal\: OK
) else (
    echo   [AVERTISSEMENT] Dossier _internal non trouve
)

echo.

REM ============================================
REM RÉSUMÉ FINAL
REM ============================================

echo.
echo ============================================
echo  BUILD TERMINE AVEC SUCCES !
echo ============================================
echo.
echo Application prete:
echo   Location: %DIST_DIR%\
echo.
echo Fichiers principaux:
dir /B "%DIST_DIR%" 2>nul | findstr /V "_internal"
echo.
echo Taille totale:
for /f "tokens=3" %%a in ('dir "%DIST_DIR%" ^| find "File(s)"') do echo   %%a bytes
echo.
echo ============================================
echo  INSTRUCTIONS DE LANCEMENT
echo ============================================
echo.
echo 1. Allez dans: %DIST_DIR%\
echo 2. Double-cliquez sur: %APP_NAME%.exe
echo 3. Le navigateur s'ouvre automatiquement
echo 4. Configurez vos identifiants via Settings
echo.
echo Pour distribuer:
echo   Copiez tout le dossier %APP_NAME%\
echo   (incluant _internal\ et autres dossiers)
echo.
echo ============================================
echo  TESTS RECOMMANDES
echo ============================================
echo.
echo Avant de distribuer, testez:
echo   1. Lancement de l'exe
echo   2. Ouverture navigateur automatique
echo   3. Configuration via Settings
echo   4. Connexion au casque
echo   5. Enregistrement session
echo   6. Telechargement CSV
echo.
echo ============================================
echo.

pause

REM ============================================
REM PROPOSITION TEST IMMEDIAT
REM ============================================

echo.
set /p LAUNCH="Voulez-vous tester l'application maintenant ? (O/N): "
if /i "%LAUNCH%"=="O" (
    echo.
    echo Lancement de %APP_NAME%...
    echo.
    cd "%DIST_DIR%"
    start %APP_NAME%.exe
    echo.
    echo L'application devrait s'ouvrir dans le navigateur.
    echo Fermez cette fenetre quand vous avez termine.
    pause
)

endlocal
