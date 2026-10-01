@echo off
REM ============================================
REM NEUROSITY MONITOR - LANCEUR SIMPLE
REM Lance l'application et ouvre le navigateur
REM ============================================

title Neurosity Monitor

echo.
echo ============================================
echo  NEUROSITY MONITOR
echo ============================================
echo.
echo Demarrage de l'application...
echo.

REM Vérifier que l'exe existe (son nom commence par la date du build)
set "APP_EXE="
for %%f in (*NeurosityMonitor.exe) do set "APP_EXE=%%f"
if not defined APP_EXE (
    echo [ERREUR] NeurosityMonitor.exe non trouve
    echo.
    echo Assurez-vous d'etre dans le bon dossier.
    echo.
    pause
    exit /b 1
)

REM Lancer l'application
start "" "%APP_EXE%"

echo L'application demarre...
echo Le navigateur devrait s'ouvrir automatiquement.
echo.
echo Si le navigateur ne s'ouvre pas, allez sur:
echo   http://localhost:5000
echo.
echo Pour arreter l'application:
echo   Fermez cette fenetre ou appuyez sur Ctrl+C
echo.
echo ============================================

REM Garder la fenêtre ouverte
pause
