@echo off
setlocal enabledelayedexpansion

REM ============================================
REM NEUROSITY MONITOR - MENU PRINCIPAL
REM Menu interactif pour gérer le projet
REM ============================================

:MENU
REM Dernier build présent dans dist\ (ex: 01_10_26_NeurosityMonitor)
set "APP_NAME="
for /f "delims=" %%d in ('dir /b /ad /o-d "dist\*NeurosityMonitor" 2^>nul') do if not defined APP_NAME set "APP_NAME=%%d"

cls
echo.
echo ============================================
echo  NEUROSITY MONITOR - MENU PRINCIPAL
echo ============================================
echo.
echo  1. Organiser le projet
echo  2. Build complet (recommande)
echo  3. Build rapide (developpement)
echo  4. Tester l'application
echo  5. Nettoyer les builds
echo  6. Lancer l'application
echo  7. Voir la structure
echo  8. Installation dependances
echo  9. Aide et documentation
echo  0. Quitter
echo.
echo ============================================
echo.

set /p CHOICE="Votre choix (0-9): "

if "%CHOICE%"=="1" goto ORGANIZE
if "%CHOICE%"=="2" goto BUILD_FULL
if "%CHOICE%"=="3" goto BUILD_QUICK
if "%CHOICE%"=="4" goto TEST
if "%CHOICE%"=="5" goto CLEAN
if "%CHOICE%"=="6" goto LAUNCH
if "%CHOICE%"=="7" goto STRUCTURE
if "%CHOICE%"=="8" goto INSTALL
if "%CHOICE%"=="9" goto HELP
if "%CHOICE%"=="0" goto EXIT

echo.
echo Choix invalide. Appuyez sur une touche...
pause >nul
goto MENU

REM ============================================
REM OPTION 1: ORGANISER LE PROJET
REM ============================================

:ORGANIZE
cls
echo.
echo ============================================
echo  ORGANISATION DU PROJET
echo ============================================
echo.

if not exist "organize_project.py" (
    echo [ERREUR] organize_project.py non trouve
    echo.
    pause
    goto MENU
)

python organize_project.py

echo.
echo ============================================
pause
goto MENU

REM ============================================
REM OPTION 2: BUILD COMPLET
REM ============================================

:BUILD_FULL
cls
echo.
echo ============================================
echo  BUILD COMPLET
echo ============================================
echo.
echo Cette operation peut prendre 5-10 minutes
echo.
set /p CONFIRM="Continuer ? (O/N): "

if /i not "%CONFIRM%"=="O" goto MENU

if not exist "build.bat" (
    echo [ERREUR] build.bat non trouve
    pause
    goto MENU
)

call build.bat

echo.
echo ============================================
pause
goto MENU

REM ============================================
REM OPTION 3: BUILD RAPIDE
REM ============================================

:BUILD_QUICK
cls
echo.
echo ============================================
echo  BUILD RAPIDE (DEVELOPPEMENT)
echo ============================================
echo.

if not exist "quick_build.bat" (
    echo [ERREUR] quick_build.bat non trouve
    pause
    goto MENU
)

call quick_build.bat

echo.
echo ============================================
pause
goto MENU

REM ============================================
REM OPTION 4: TESTER L'APPLICATION
REM ============================================

:TEST
cls
echo.
echo ============================================
echo  TEST DE L'APPLICATION
echo ============================================
echo.

if not exist "dist\%APP_NAME%\%APP_NAME%.exe" (
    echo [ERREUR] Application non compilée
    echo.
    echo Compilez d'abord l'application avec l'option 2 ou 3
    pause
    goto MENU
)

if not exist "test_application.py" (
    echo [ERREUR] test_application.py non trouve
    pause
    goto MENU
)

python test_application.py

echo.
echo ============================================
pause
goto MENU

REM ============================================
REM OPTION 5: NETTOYER
REM ============================================

:CLEAN
cls
echo.
echo ============================================
echo  NETTOYAGE DES BUILDS
echo ============================================
echo.
echo Cette operation va supprimer:
echo   - build/
echo   - dist/
echo   - __pycache__/
echo   - *.spec generes
echo.
set /p CONFIRM="Confirmer le nettoyage ? (O/N): "

if /i not "%CONFIRM%"=="O" goto MENU

echo.
echo Nettoyage en cours...

if exist "build" (
    rmdir /s /q build
    echo   - build/ supprime
)

if exist "dist" (
    rmdir /s /q dist
    echo   - dist/ supprime
)

if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo   - __pycache__/ supprime
)

REM Nettoyer les __pycache__ dans les sous-dossiers
for /d /r %%d in (__pycache__) do @if exist "%%d" (
    rmdir /s /q "%%d"
)

if exist "NeurosityMonitor.spec" (
    del /q NeurosityMonitor.spec
    echo   - NeurosityMonitor.spec supprime
)

echo.
echo Nettoyage termine!
echo.
pause
goto MENU

REM ============================================
REM OPTION 6: LANCER L'APPLICATION
REM ============================================

:LAUNCH
cls
echo.
echo ============================================
echo  LANCEMENT DE L'APPLICATION
echo ============================================
echo.

if exist "dist\%APP_NAME%\%APP_NAME%.exe" (
    echo Lancement de l'application compilée...
    echo.
    cd dist\%APP_NAME%
    start "" "%APP_NAME%.exe"
    cd ..\..
    echo.
    echo Application lancée!
    echo Le navigateur devrait s'ouvrir automatiquement.
    echo.
) else if exist "app.py" (
    echo Application non compilée.
    echo Lancement en mode développement...
    echo.
    set /p DEVMODE="Lancer en mode dev ? (O/N): "
    if /i "!DEVMODE!"=="O" (
        if exist ".venv\Scripts\activate.bat" (
            call .venv\Scripts\activate.bat
        )
        python app.py
    )
) else (
    echo [ERREUR] Application non trouvée
    echo.
    echo Compilez d'abord avec l'option 2 ou 3
)

echo.
pause
goto MENU

REM ============================================
REM OPTION 7: STRUCTURE
REM ============================================

:STRUCTURE
cls
echo.
echo ============================================
echo  STRUCTURE DU PROJET
echo ============================================
echo.

echo Structure actuelle:
echo.
tree /F /A | more

echo.
echo ============================================
echo.

if defined APP_NAME (
    echo Structure de la distribution:
    echo.
    cd dist\%APP_NAME%
    dir /B
    cd ..\..
    echo.
)

pause
goto MENU

REM ============================================
REM OPTION 8: INSTALLATION
REM ============================================

:INSTALL
cls
echo.
echo ============================================
echo  INSTALLATION DES DEPENDANCES
echo ============================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python non installé
    echo.
    echo Installez Python depuis: https://www.python.org/downloads/
    pause
    goto MENU
)

echo Python detecte:
python --version
echo.

REM Créer/activer venv
if not exist ".venv" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv
    echo.
)

call .venv\Scripts\activate.bat
echo Environnement virtuel active
echo.

REM Installer dépendances
echo Installation des dependances...
echo.

if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo [AVERTISSEMENT] requirements.txt non trouve
    echo Installation manuelle des packages principaux...
    pip install Flask Flask-SocketIO neurosity cryptography python-dotenv pandas numpy requests
)

echo.
echo Installation de PyInstaller...
pip install pyinstaller

echo.
echo ============================================
echo  Installation terminée!
echo ============================================
echo.

pause
goto MENU

REM ============================================
REM OPTION 9: AIDE
REM ============================================

:HELP
cls
echo.
echo ============================================
echo  AIDE ET DOCUMENTATION
echo ============================================
echo.
echo Documentation disponible:
echo.

if exist "README.md" (
    echo   [X] README.md - Vue d'ensemble du projet
) else (
    echo   [ ] README.md - Non trouve
)

if exist "GUIDE_INSTALLATION.md" (
    echo   [X] GUIDE_INSTALLATION.md - Guide complet
) else (
    echo   [ ] GUIDE_INSTALLATION.md - Non trouve
)

echo.
echo ============================================
echo  WORKFLOW RECOMMANDE
echo ============================================
echo.
echo 1. Installation (option 8)
echo    - Installe Python et dependances
echo.
echo 2. Organisation (option 1)
echo    - Organise les fichiers dans la bonne structure
echo.
echo 3. Build complet (option 2)
echo    - Compile l'application en .exe
echo.
echo 4. Test (option 4)
echo    - Verifie que tout fonctionne
echo.
echo 5. Lancement (option 6)
echo    - Lance l'application
echo.
echo ============================================
echo  LIENS UTILES
echo ============================================
echo.
echo Documentation Neurosity:
echo   https://docs.neurosity.co
echo.
echo SDK Python Neurosity:
echo   https://github.com/neurosity/neurosity-python
echo.
echo Support Neurosity:
echo   support@neurosity.co
echo.
echo ============================================
echo.

set /p OPEN_README="Ouvrir README.md ? (O/N): "
if /i "%OPEN_README%"=="O" (
    if exist "README.md" (
        start README.md
    )
)

pause
goto MENU

REM ============================================
REM OPTION 0: QUITTER
REM ============================================

:EXIT
cls
echo.
echo ============================================
echo  NEUROSITY MONITOR
echo ============================================
echo.
echo Merci d'avoir utilise le menu!
echo.
echo Pour relancer: menu.bat
echo.
echo ============================================
echo.
timeout /t 2 >nul
exit /b 0

endlocal
