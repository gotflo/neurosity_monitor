NEUROSITY CROWN MONITOR
======================

🧠 Application de monitoring pour casque Neurosity Crown

INSTALLATION RAPIDE
-------------------
1. Editez le fichier .env.template avec vos informations Neurosity
2. Renommez .env.template en .env
3. Double-cliquez sur NeurosityMonitor.exe
4. L'application s'ouvre automatiquement dans votre navigateur

CONFIGURATION NEUROSITY
----------------------
Vous devez avoir:
- Un compte Neurosity
- Un casque Neurosity Crown
- L'ID de votre casque (visible dans l'app mobile Neurosity)

UTILISATION
-----------
1. Allumez votre casque Neurosity Crown
2. Portez-le correctement (toutes les électrodes doivent être en contact)
3. Lancez NeurosityMonitor.exe
4. Cliquez sur "Connecter" dans l'interface
5. Les données s'affichent en temps réel !

FONCTIONNALITÉS
---------------
✓ Visualisation temps réel des ondes cérébrales
✓ Mesure du calme et de la concentration
✓ Affichage de la qualité du signal par électrode
✓ Enregistrement des sessions en CSV
✓ Export des données pour analyse
✓ Graphiques EEG bruts

CONFIGURATION AVANCÉE
--------------------
Port par défaut: 5000
Pour changer le port, éditez FLASK_PORT dans le fichier .env

PROBLÈMES COURANTS
-----------------
- "Casque non détecté": Vérifiez qu'il est allumé et bien positionné
- "Erreur de connexion": Vérifiez vos identifiants dans .env
- Port déjà utilisé: Changez FLASK_PORT dans .env

STRUCTURE DES DOSSIERS
---------------------
- data/     : Sessions enregistrées (fichiers CSV)
- logs/     : Fichiers de logs
- .env      : Configuration (à créer depuis .env.template)

SUPPORT
-------
Pour toute question, consultez la documentation Neurosity:
https://docs.neurosity.co/

Version 2.0 - Optimisée pour Windows
