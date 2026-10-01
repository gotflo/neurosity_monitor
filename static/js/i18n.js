/**
 * NEUROSITY MONITOR - MOTEUR DE TRADUCTION (i18n)
 * ------------------------------------------------
 * Langue par défaut : FR. Langues supportées : FR, EN.
 *
 * Ce fichier doit être chargé AVANT tous les autres scripts de l'application.
 *
 * Utilisation dans le HTML :
 *   <span data-i18n="cle"></span>                     -> textContent
 *   <span data-i18n-html="cle"></span>                -> innerHTML
 *   <input data-i18n-attr="placeholder:cle,title:cle2">-> attributs
 *   <div data-i18n-switcher></div>                    -> sélecteur de langue
 *
 * Utilisation dans le JS :
 *   t('cle')                    -> chaîne traduite
 *   t('cle', { nom: 'valeur' }) -> interpolation {nom}
 *   I18n.plural('cle', n)       -> gestion cle.zero / cle.one / cle.other
 *   I18n.onChange(fn)           -> callback au changement de langue
 */

(function (global) {
  'use strict';

  const DEFAULT_LANG = 'fr';
  const SUPPORTED = ['fr', 'en'];
  const STORAGE_KEY = 'neuro_lang';
  const COOKIE_KEY = 'neuro_lang';

  // ===============================================
  // DICTIONNAIRES
  // ===============================================

  const DICT = {
    fr: {
      // --- Commun ---
      'common.appName': 'Neurosity Monitor',
      'common.language': 'Langue',
      'common.languageName': 'Français',
      'common.close': 'Fermer',

      // --- Dashboard : structure ---
      'index.title': 'Tableau de bord - Neurosity Crown Monitor',
      'index.meta.description': 'Monitor en temps réel pour casque Neurosity Crown',
      'index.loader': "Chargement de l'interface...",
      'index.device': 'Dispositif',
      'index.recording': 'Enregistrement...',

      'status.connected': 'Connecté',
      'status.disconnected': 'Déconnecté',

      'btn.settings': 'Configuration',
      'btn.settings.title': 'Configuration',
      'btn.connect': 'Connecter',
      'btn.connect.title': 'Connecter (Ctrl+K)',
      'btn.disconnect': 'Déconnecter',
      'btn.connecting': 'Connexion...',
      'btn.record': 'Enregistrer',
      'btn.record.title': 'Enregistrer (Ctrl+R)',
      'btn.recordStop': 'Arrêter',
      'btn.download': 'Télécharger',
      'btn.download.title': 'Télécharger',

      'metric.calm': 'Calme',
      'metric.focus': 'Concentration',

      'chart.brainwaves.title': 'Ondes Cérébrales en Temps Réel',
      'chart.eegRaw.title': 'Signaux EEG Bruts',
      'chart.lastUpdate': 'Dernière mise à jour : {value}',
      'chart.power.label': 'Puissance (μV²/Hz)',

      'sessions.title': 'Sessions Enregistrées',
      'sessions.count.zero': 'Aucune session',
      'sessions.count.one': '1 session',
      'sessions.count.other': '{n} sessions',
      'sessions.emptyHint': 'Connectez votre casque pour voir les sessions',
      'sessions.empty': 'Aucune session enregistrée',
      'sessions.emptyCreate': 'Connectez votre casque pour créer une session',
      'sessions.stat.sessions': 'sessions',
      'sessions.stat.stored': 'stockés',
      'sessions.refresh': 'Actualiser',
      'sessions.refreshing': 'Actualisation...',
      'sessions.visualize': 'Visualiser',
      'sessions.visualize.title': 'Visualiser les données',
      'sessions.csv.title': 'Télécharger le CSV',
      'sessions.loadError': 'Erreur de chargement',
      'sessions.date': 'Date',
      'sessions.time': 'Heure',

      'system.title': 'Statut du Système',
      'system.connection': 'État de la connexion',
      'system.monitoring': 'Monitoring actif',
      'system.battery': 'Batterie',
      'system.active': 'Actif',
      'system.stopped': 'Arrêté',
      'signal.title': 'Qualité du Signal',

      'footer.tagline': 'Monitoring en temps réel',

      // --- Dashboard : messages ---
      'toast.ws.connected': 'Connexion WebSocket établie',
      'toast.ws.lost': '🔌 Connexion WebSocket perdue',
      'toast.monitoring.started': 'Monitoring démarré !',
      'toast.monitoring.stopped': 'Monitoring arrêté',
      'toast.error': 'Erreur : {message}',
      'toast.connecting': 'Connexion au casque Neurosity...',
      'toast.connected': 'Casque connecté !',
      'toast.connectError': 'Erreur de connexion',
      'toast.networkError': 'Erreur réseau',
      'toast.disconnected': '🔌 Casque déconnecté',
      'toast.connectFirst': "Connectez d'abord votre casque",
      'toast.recording.starting': "🎬 Démarrage de l'enregistrement...",
      'toast.recording.stopping': "🎬 Arrêt de l'enregistrement...",
      'toast.recording.started': 'Enregistrement démarré !',
      'toast.recording.stopped': 'Enregistrement arrêté',
      'toast.unknownError': 'Erreur inconnue',
      'toast.searchingSession': 'Recherche de la dernière session...',
      'toast.downloading': 'Téléchargement : {file}',
      'toast.noSession': 'Aucune session disponible',
      'toast.downloadError': 'Erreur de téléchargement',
      'toast.opening': '📊 Ouverture de la visualisation...',
      'toast.refreshingSessions': 'Actualisation des sessions...',
      'toast.welcome': 'Application prête ! Allumez votre casque Neurosity puis cliquez sur « Connecter »',
      'toast.langChanged': 'Langue : Français',
      'confirm.disconnect': 'Êtes-vous sûr de vouloir déconnecter le casque ?',
      'confirm.unload': 'Un enregistrement est en cours. Êtes-vous sûr de vouloir fermer ?',

      // --- Configuration ---
      'settings.title': 'Configuration - Neurosity Crown Monitor',
      'settings.heading': 'Configuration Neurosity',
      'settings.subtitle': 'Connectez votre casque Crown pour commencer',
      'settings.current': 'Configuration actuelle',
      'settings.current.email': 'Email :',
      'settings.current.deviceId': 'Device ID :',
      'settings.deviceId': 'Device ID',
      'settings.deviceId.placeholder': 'Ex : 442b4e3d8a0f...',
      'settings.deviceId.help': 'Trouvez votre Device ID sur',
      'settings.email': 'Email Neurosity',
      'settings.email.placeholder': 'votre.email@example.com',
      'settings.email.help': 'L\'email de votre compte Neurosity',
      'settings.password': 'Mot de passe',
      'settings.password.help': 'Votre mot de passe Neurosity (stocké de manière sécurisée)',
      'settings.optional': 'Paramètres optionnels',
      'settings.autoConnect': 'Connexion automatique au démarrage',
      'settings.remember': 'Mémoriser mes identifiants (chiffrés)',
      'settings.language': 'Langue de l\'interface',
      'settings.language.help': "S'applique à toute la plateforme, graphiques inclus",
      'settings.test': 'Tester la connexion',
      'settings.testing': 'Test en cours...',
      'settings.save': 'Mettre à jour et continuer',
      'settings.saving': 'Chargement...',
      'settings.back': '← Retour à l\'application',
      'settings.clear': '🗑️ Effacer la configuration',
      'settings.toast.welcome': 'Configurez vos identifiants Neurosity',
      'settings.toast.saved': 'Configuration sauvegardée avec succès !',
      'settings.toast.saveError': 'Erreur lors de la sauvegarde',
      'settings.toast.serverError': 'Erreur de connexion au serveur',
      'settings.toast.fillAll': 'Veuillez remplir tous les champs',
      'settings.toast.fillRequired': 'Veuillez remplir tous les champs obligatoires',
      'settings.toast.testing': 'Test de connexion en cours...',
      'settings.toast.testSuccess': '✅ Connexion réussie !',
      'settings.toast.testSuccessDetail': '✅ Test réussi ! Les identifiants sont valides.',
      'settings.toast.testFailed': '❌ Échec de connexion',
      'settings.toast.testError': 'Erreur lors du test',
      'settings.toast.testErrorDetail': 'Erreur lors du test de connexion',
      'settings.toast.invalidCredentials': 'Identifiants invalides',
      'settings.toast.invalidEmail': 'Email invalide',
      'settings.toast.deviceIdShort': 'Device ID trop court',
      'settings.toast.cleared': 'Configuration effacée',
      'settings.toast.clearError': 'Erreur lors de la suppression',
      'settings.toast.connectionError': 'Erreur de connexion',
      'settings.confirm.clear': 'Êtes-vous sûr de vouloir effacer toute la configuration ?',

      // --- Visualiseur CSV ---
      'viewer.title': 'Visualisation CSV - Neurosity',
      'viewer.heading': 'Visualisation des données EEG',
      'viewer.file': 'Fichier : {name}',
      'viewer.duration': 'Durée :',
      'viewer.points': 'Lignes :',
      'viewer.points.unit': 'points de données',
      'viewer.back': '← Retour au tableau de bord',
      'viewer.durationValue': '{m}m {s}s',

      'filter.title': 'Filtrage temporel',
      'filter.t1': 'Temps de départ (t1) en secondes',
      'filter.t2': 'Temps d\'arrivée (t2) en secondes',
      'filter.t2.placeholder': 'Fin',
      'filter.apply': 'Appliquer le filtre',
      'filter.reset': 'Réinitialiser',
      'filter.none': 'Aucun filtre appliqué - Affichage de toutes les données',
      'filter.active': '✅ Filtre actif : <strong>{t1}s → {t2}s</strong> (durée : {duration}s, {points} points)',
      'filter.error.t1': '❌ t1 doit être positif',
      'filter.error.t2': '❌ t2 doit être supérieur à t1',
      'filter.warn.t2': '⚠️ t2 ajusté à la durée maximale',
      'filter.applied': '✅ Filtre appliqué avec succès',
      'filter.wasReset': '🔄 Filtre réinitialisé',

      'replay.title': '⏯ Replay temporel',
      'replay.play': 'Lecture / Pause',
      'replay.stop': 'Stop (retour au début)',
      'replay.speed': 'Vitesse de lecture',
      'replay.hint': '🖱 <strong>Zoom :</strong> molette de la souris sur un graphique &nbsp;•&nbsp; <strong>Réinitialiser :</strong> double-clic sur un graphique &nbsp;•&nbsp; <strong>Lecture / Pause :</strong> barre espace',

      'viewer.save': '💾 Sauvegarder',
      'viewer.saved': '💾 Graphique sauvegardé : {file}',
      'viewer.saveError': '❌ Erreur lors de la sauvegarde',
      'viewer.chartNotFound': '❌ Graphique non trouvé',
      'viewer.error': 'Erreur',
      'viewer.error.noFile': 'Aucun fichier spécifié dans l\'URL',
      'viewer.error.server': 'Erreur serveur : {status}',

      // Cartes de graphiques
      'card.cognitive.title': 'États Cognitifs',
      'card.cognitive.desc': 'Niveau de calme et de concentration dans le temps',
      'card.cognitive.file': 'etats-cognitifs',
      'card.bands.title': 'Bandes de Fréquences EEG',
      'card.bands.desc': 'Évolution des ondes cérébrales (Delta, Theta, Alpha, Beta, Gamma)',
      'card.bands.file': 'bandes-frequences',
      'card.deltaBeta.title': 'Charge Affective',
      'card.deltaBeta.desc': 'Ratio Delta/Beta • élevé quand le sujet se déconnecte de l\'activité cognitive (réseau par défaut)',
      'card.deltaBeta.file': 'charge-affective',
      'card.cognitiveLoad.title': 'Charge Cognitive',
      'card.cognitiveLoad.desc': 'Ratio Theta/Alpha • augmente avec l\'effort mental',
      'card.cognitiveLoad.file': 'charge-cognitive',
      'card.ratios.title': 'Ratios Cognitifs',
      'card.ratios.desc': 'Alpha/Beta (stress) • Theta/Beta (baisse d\'attention) • Activation globale',
      'card.ratios.file': 'ratios-cognitifs',
      'card.relative.title': 'Puissances Relatives des Bandes',
      'card.relative.desc': 'Distribution en pourcentage de chaque bande de fréquence',
      'card.relative.file': 'puissances-relatives',
      'card.derived.title': 'Métriques Cognitives Dérivées',
      'card.derived.desc': 'Charge cognitive • Engagement • Relaxation • Stress',
      'card.derived.file': 'metriques-derivees',
      'card.asymmetry.title': 'Asymétries EEG (Émotion/Motivation)',
      'card.asymmetry.desc': 'Asymétrie frontale (F5-F6) • Centrale (C3-C4) • Pariétale (PO3-PO4)',
      'card.asymmetry.file': 'asymetries-eeg',
      'card.eegRaw.title': 'Signaux EEG Bruts',
      'card.eegRaw.desc': 'Signaux bruts par électrode (8 canaux)',
      'card.eegRaw.file': 'signaux-eeg-bruts',

      // Axes et séries des graphiques
      'axis.time': 'Temps',
      'axis.probability': 'Probabilité (%)',
      'axis.power': 'Puissance (µV²)',
      'axis.relativePower': 'Puissance relative (%)',
      'axis.ratio': 'Ratio',
      'axis.deltaBetaRatio': 'Ratio Delta/Beta',
      'axis.thetaAlphaRatio': 'Ratio Theta/Alpha',
      'axis.normalized': 'Valeur normalisée',
      'axis.asymmetry': 'Asymétrie (valeur normalisée)',
      'axis.amplitude': 'Amplitude (µV)',

      'series.calm': 'Calme',
      'series.focus': 'Concentration',
      'series.delta': 'Delta (0,5-4 Hz)',
      'series.theta': 'Theta (4-8 Hz)',
      'series.alpha': 'Alpha (8-13 Hz)',
      'series.beta': 'Beta (13-30 Hz)',
      'series.gamma': 'Gamma (30+ Hz)',
      'series.deltaBeta': 'Charge Affective (Delta/Beta)',
      'series.thetaBeta': 'Theta/Beta - Baisse d\'attention',
      'series.alphaTheta': 'Alpha/Theta - Fatigue',
      'series.betaAlpha': 'Beta/Alpha - Vigilance',
      'series.slowing': 'Ralentissement EEG — (δ+θ)/(α+β) — haut = somnolence',
      'series.engagement': 'Engagement',
      'series.cognitiveLoad': 'Charge Cognitive (Theta/Alpha)',
      'series.relaxation': 'Relaxation',
      'series.asymFrontal': 'Asymétrie Frontale (ln F6 − ln F5)',
      'series.asymCentral': 'Asymétrie Centrale (ln C4 − ln C3)',
      'series.asymParietal': 'Asymétrie Pariétale (ln PO4 − ln PO3)',
      'series.deltaRelative': 'Delta relative (%)',
      'series.thetaRelative': 'Theta relative (%)',
      'series.alphaRelative': 'Alpha relative (%)',
      'series.betaRelative': 'Beta relative (%)',
      'series.gammaRelative': 'Gamma relative (%)',

      'tooltip.drowsiness': ' (somnolence)',
      'tooltip.relaxation': ' (relaxation)',
      'tooltip.activeWake': ' (éveil actif)',
      'tooltip.na': 'N/A',

      // --- Messages provenant du serveur ---
      'server.missing_config': 'Configuration manquante. Allez dans Configuration.',
      'server.device_not_detected': "Casque non détecté. Vérifiez qu'il est allumé et porté correctement.",
      'server.device_connected': 'Casque Neurosity connecté !',
      'server.not_connected': 'Non connecté',
      'server.module_not_ready': 'Module non initialisé',
      'server.sdk_missing': 'SDK Neurosity non installé. Installez-le avec : pip install neurosity',
      'server.config_saved': 'Configuration sauvegardée',
      'server.save_failed': 'Erreur de sauvegarde',
      'server.test_success': 'Connexion réussie !',
      'server.file_not_found': 'Fichier non trouvé',
      'server.empty_csv': 'Fichier CSV vide',
      'server.error': 'Erreur',
      'server.language_saved': 'Langue enregistrée',
      'server.unsupported_language': 'Langue non supportée'
    },

    en: {
      // --- Common ---
      'common.appName': 'Neurosity Monitor',
      'common.language': 'Language',
      'common.languageName': 'English',
      'common.close': 'Close',

      // --- Dashboard: structure ---
      'index.title': 'Dashboard - Neurosity Crown Monitor',
      'index.meta.description': 'Real-time monitor for the Neurosity Crown headset',
      'index.loader': 'Loading interface...',
      'index.device': 'Device',
      'index.recording': 'Recording...',

      'status.connected': 'Connected',
      'status.disconnected': 'Disconnected',

      'btn.settings': 'Settings',
      'btn.settings.title': 'Settings',
      'btn.connect': 'Connect',
      'btn.connect.title': 'Connect (Ctrl+K)',
      'btn.disconnect': 'Disconnect',
      'btn.connecting': 'Connecting...',
      'btn.record': 'Record',
      'btn.record.title': 'Record (Ctrl+R)',
      'btn.recordStop': 'Stop',
      'btn.download': 'Download',
      'btn.download.title': 'Download',

      'metric.calm': 'Calm',
      'metric.focus': 'Focus',

      'chart.brainwaves.title': 'Real-Time Brainwaves',
      'chart.eegRaw.title': 'Raw EEG Signals',
      'chart.lastUpdate': 'Last update: {value}',
      'chart.power.label': 'Power (μV²/Hz)',

      'sessions.title': 'Recorded Sessions',
      'sessions.count.zero': 'No session',
      'sessions.count.one': '1 session',
      'sessions.count.other': '{n} sessions',
      'sessions.emptyHint': 'Connect your headset to see the sessions',
      'sessions.empty': 'No recorded session',
      'sessions.emptyCreate': 'Connect your headset to create a session',
      'sessions.stat.sessions': 'sessions',
      'sessions.stat.stored': 'stored',
      'sessions.refresh': 'Refresh',
      'sessions.refreshing': 'Refreshing...',
      'sessions.visualize': 'Visualize',
      'sessions.visualize.title': 'Visualize the data',
      'sessions.csv.title': 'Download the CSV',
      'sessions.loadError': 'Loading error',
      'sessions.date': 'Date',
      'sessions.time': 'Time',

      'system.title': 'System Status',
      'system.connection': 'Connection state',
      'system.monitoring': 'Monitoring active',
      'system.battery': 'Battery',
      'system.active': 'Active',
      'system.stopped': 'Stopped',
      'signal.title': 'Signal Quality',

      'footer.tagline': 'Real-time monitoring',

      // --- Dashboard: messages ---
      'toast.ws.connected': 'WebSocket connection established',
      'toast.ws.lost': '🔌 WebSocket connection lost',
      'toast.monitoring.started': 'Monitoring started!',
      'toast.monitoring.stopped': 'Monitoring stopped',
      'toast.error': 'Error: {message}',
      'toast.connecting': 'Connecting to the Neurosity headset...',
      'toast.connected': 'Headset connected!',
      'toast.connectError': 'Connection error',
      'toast.networkError': 'Network error',
      'toast.disconnected': '🔌 Headset disconnected',
      'toast.connectFirst': 'Connect your headset first',
      'toast.recording.starting': '🎬 Starting the recording...',
      'toast.recording.stopping': '🎬 Stopping the recording...',
      'toast.recording.started': 'Recording started!',
      'toast.recording.stopped': 'Recording stopped',
      'toast.unknownError': 'Unknown error',
      'toast.searchingSession': 'Looking for the latest session...',
      'toast.downloading': 'Downloading: {file}',
      'toast.noSession': 'No session available',
      'toast.downloadError': 'Download error',
      'toast.opening': '📊 Opening the visualization...',
      'toast.refreshingSessions': 'Refreshing the sessions...',
      'toast.welcome': 'Application ready! Turn on your Neurosity headset then click "Connect"',
      'toast.langChanged': 'Language: English',
      'confirm.disconnect': 'Are you sure you want to disconnect the headset?',
      'confirm.unload': 'A recording is in progress. Are you sure you want to close?',

      // --- Settings ---
      'settings.title': 'Settings - Neurosity Crown Monitor',
      'settings.heading': 'Neurosity Settings',
      'settings.subtitle': 'Connect your Crown headset to get started',
      'settings.current': 'Current configuration',
      'settings.current.email': 'Email:',
      'settings.current.deviceId': 'Device ID:',
      'settings.deviceId': 'Device ID',
      'settings.deviceId.placeholder': 'E.g. 442b4e3d8a0f...',
      'settings.deviceId.help': 'Find your Device ID on',
      'settings.email': 'Neurosity email',
      'settings.email.placeholder': 'your.email@example.com',
      'settings.email.help': 'The email of your Neurosity account',
      'settings.password': 'Password',
      'settings.password.help': 'Your Neurosity password (stored securely)',
      'settings.optional': 'Optional settings',
      'settings.autoConnect': 'Connect automatically on startup',
      'settings.remember': 'Remember my credentials (encrypted)',
      'settings.language': 'Interface language',
      'settings.language.help': 'Applies to the whole platform, charts included',
      'settings.test': 'Test the connection',
      'settings.testing': 'Testing...',
      'settings.save': 'Update and continue',
      'settings.saving': 'Loading...',
      'settings.back': '← Back to the application',
      'settings.clear': '🗑️ Clear the configuration',
      'settings.toast.welcome': 'Set up your Neurosity credentials',
      'settings.toast.saved': 'Configuration saved successfully!',
      'settings.toast.saveError': 'Error while saving',
      'settings.toast.serverError': 'Could not reach the server',
      'settings.toast.fillAll': 'Please fill in every field',
      'settings.toast.fillRequired': 'Please fill in every required field',
      'settings.toast.testing': 'Connection test in progress...',
      'settings.toast.testSuccess': '✅ Connection successful!',
      'settings.toast.testSuccessDetail': '✅ Test passed! The credentials are valid.',
      'settings.toast.testFailed': '❌ Connection failed',
      'settings.toast.testError': 'Error during the test',
      'settings.toast.testErrorDetail': 'Error during the connection test',
      'settings.toast.invalidCredentials': 'Invalid credentials',
      'settings.toast.invalidEmail': 'Invalid email',
      'settings.toast.deviceIdShort': 'Device ID too short',
      'settings.toast.cleared': 'Configuration cleared',
      'settings.toast.clearError': 'Error while deleting',
      'settings.toast.connectionError': 'Connection error',
      'settings.confirm.clear': 'Are you sure you want to erase the whole configuration?',

      // --- CSV viewer ---
      'viewer.title': 'CSV Visualization - Neurosity',
      'viewer.heading': 'EEG Data Visualization',
      'viewer.file': 'File: {name}',
      'viewer.duration': 'Duration:',
      'viewer.points': 'Rows:',
      'viewer.points.unit': 'data points',
      'viewer.back': '← Back to the dashboard',
      'viewer.durationValue': '{m}m {s}s',

      'filter.title': 'Time filtering',
      'filter.t1': 'Start time (t1) in seconds',
      'filter.t2': 'End time (t2) in seconds',
      'filter.t2.placeholder': 'End',
      'filter.apply': 'Apply the filter',
      'filter.reset': 'Reset',
      'filter.none': 'No filter applied - Showing all the data',
      'filter.active': '✅ Active filter: <strong>{t1}s → {t2}s</strong> (duration: {duration}s, {points} points)',
      'filter.error.t1': '❌ t1 must be positive',
      'filter.error.t2': '❌ t2 must be greater than t1',
      'filter.warn.t2': '⚠️ t2 clamped to the maximum duration',
      'filter.applied': '✅ Filter applied successfully',
      'filter.wasReset': '🔄 Filter reset',

      'replay.title': '⏯ Time replay',
      'replay.play': 'Play / Pause',
      'replay.stop': 'Stop (back to the start)',
      'replay.speed': 'Playback speed',
      'replay.hint': '🖱 <strong>Zoom:</strong> mouse wheel over a chart &nbsp;•&nbsp; <strong>Reset:</strong> double-click on a chart &nbsp;•&nbsp; <strong>Play / Pause:</strong> spacebar',

      'viewer.save': '💾 Save',
      'viewer.saved': '💾 Chart saved: {file}',
      'viewer.saveError': '❌ Error while saving',
      'viewer.chartNotFound': '❌ Chart not found',
      'viewer.error': 'Error',
      'viewer.error.noFile': 'No file specified in the URL',
      'viewer.error.server': 'Server error: {status}',

      // Chart cards
      'card.cognitive.title': 'Cognitive States',
      'card.cognitive.desc': 'Calm and focus levels over time',
      'card.cognitive.file': 'cognitive-states',
      'card.bands.title': 'EEG Frequency Bands',
      'card.bands.desc': 'Brainwave evolution (Delta, Theta, Alpha, Beta, Gamma)',
      'card.bands.file': 'frequency-bands',
      'card.deltaBeta.title': 'Affective Load',
      'card.deltaBeta.desc': 'Delta/Beta ratio • high when the subject disconnects from cognitive activity (default mode network)',
      'card.deltaBeta.file': 'affective-load',
      'card.cognitiveLoad.title': 'Cognitive Load',
      'card.cognitiveLoad.desc': 'Theta/Alpha ratio • rises with mental effort',
      'card.cognitiveLoad.file': 'cognitive-load',
      'card.ratios.title': 'Cognitive Ratios',
      'card.ratios.desc': 'Alpha/Beta (stress) • Theta/Beta (attention drop) • Global activation',
      'card.ratios.file': 'cognitive-ratios',
      'card.relative.title': 'Relative Band Powers',
      'card.relative.desc': 'Percentage distribution of each frequency band',
      'card.relative.file': 'relative-powers',
      'card.derived.title': 'Derived Cognitive Metrics',
      'card.derived.desc': 'Cognitive load • Engagement • Relaxation • Stress',
      'card.derived.file': 'derived-metrics',
      'card.asymmetry.title': 'EEG Asymmetries (Emotion/Motivation)',
      'card.asymmetry.desc': 'Frontal (F5-F6) • Central (C3-C4) • Parietal (PO3-PO4) asymmetry',
      'card.asymmetry.file': 'eeg-asymmetries',
      'card.eegRaw.title': 'Raw EEG Signals',
      'card.eegRaw.desc': 'Raw signals per electrode (8 channels)',
      'card.eegRaw.file': 'raw-eeg-signals',

      // Chart axes and series
      'axis.time': 'Time',
      'axis.probability': 'Probability (%)',
      'axis.power': 'Power (µV²)',
      'axis.relativePower': 'Relative power (%)',
      'axis.ratio': 'Ratio',
      'axis.deltaBetaRatio': 'Delta/Beta ratio',
      'axis.thetaAlphaRatio': 'Theta/Alpha ratio',
      'axis.normalized': 'Normalized value',
      'axis.asymmetry': 'Asymmetry (normalized value)',
      'axis.amplitude': 'Amplitude (µV)',

      'series.calm': 'Calm',
      'series.focus': 'Focus',
      'series.delta': 'Delta (0.5-4 Hz)',
      'series.theta': 'Theta (4-8 Hz)',
      'series.alpha': 'Alpha (8-13 Hz)',
      'series.beta': 'Beta (13-30 Hz)',
      'series.gamma': 'Gamma (30+ Hz)',
      'series.deltaBeta': 'Affective Load (Delta/Beta)',
      'series.thetaBeta': 'Theta/Beta - Attention drop',
      'series.alphaTheta': 'Alpha/Theta - Fatigue',
      'series.betaAlpha': 'Beta/Alpha - Vigilance',
      'series.slowing': 'EEG slowing — (δ+θ)/(α+β) — high = drowsiness',
      'series.engagement': 'Engagement',
      'series.cognitiveLoad': 'Cognitive Load (Theta/Alpha)',
      'series.relaxation': 'Relaxation',
      'series.asymFrontal': 'Frontal Asymmetry (ln F6 − ln F5)',
      'series.asymCentral': 'Central Asymmetry (ln C4 − ln C3)',
      'series.asymParietal': 'Parietal Asymmetry (ln PO4 − ln PO3)',
      'series.deltaRelative': 'Delta relative (%)',
      'series.thetaRelative': 'Theta relative (%)',
      'series.alphaRelative': 'Alpha relative (%)',
      'series.betaRelative': 'Beta relative (%)',
      'series.gammaRelative': 'Gamma relative (%)',

      'tooltip.drowsiness': ' (drowsiness)',
      'tooltip.relaxation': ' (relaxation)',
      'tooltip.activeWake': ' (active wakefulness)',
      'tooltip.na': 'N/A',

      // --- Messages coming from the server ---
      'server.missing_config': 'Missing configuration. Go to Settings.',
      'server.device_not_detected': 'Headset not detected. Make sure it is turned on and correctly worn.',
      'server.device_connected': 'Neurosity headset connected!',
      'server.not_connected': 'Not connected',
      'server.module_not_ready': 'Module not initialized',
      'server.sdk_missing': 'Neurosity SDK not installed. Install it with: pip install neurosity',
      'server.config_saved': 'Configuration saved',
      'server.save_failed': 'Save error',
      'server.test_success': 'Connection successful!',
      'server.file_not_found': 'File not found',
      'server.empty_csv': 'Empty CSV file',
      'server.error': 'Error',
      'server.language_saved': 'Language saved',
      'server.unsupported_language': 'Unsupported language'
    }
  };

  const LOCALES = { fr: 'fr-FR', en: 'en-US' };

  // ===============================================
  // ÉTAT
  // ===============================================

  let currentLang = DEFAULT_LANG;
  const listeners = [];

  function readCookie(name) {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : null;
  }

  function writeCookie(name, value) {
    document.cookie = `${name}=${encodeURIComponent(value)};path=/;max-age=31536000;SameSite=Lax`;
  }

  function normalize(lang) {
    if (!lang) return null;
    const short = String(lang).toLowerCase().slice(0, 2);
    return SUPPORTED.indexOf(short) !== -1 ? short : null;
  }

  function detectInitialLang() {
    let stored = null;
    try {
      stored = normalize(localStorage.getItem(STORAGE_KEY));
    } catch (e) {
      stored = null;
    }
    // Le serveur peut pré-positionner la langue via l'attribut lang du <html>
    const fromCookie = normalize(readCookie(COOKIE_KEY));
    const fromDom = normalize(document.documentElement.getAttribute('lang'));
    return stored || fromCookie || fromDom || DEFAULT_LANG;
  }

  // ===============================================
  // TRADUCTION
  // ===============================================

  function translate(key, vars) {
    const table = DICT[currentLang] || DICT[DEFAULT_LANG];
    let value = table[key];

    if (value === undefined) {
      value = DICT[DEFAULT_LANG][key];
    }
    if (value === undefined) {
      console.warn(`[i18n] Clé manquante : ${key}`);
      return key;
    }

    if (vars) {
      value = value.replace(/\{(\w+)\}/g, (match, name) =>
        Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : match
      );
    }
    return value;
  }

  function plural(baseKey, count, vars) {
    const suffix = count === 0 ? '.zero' : (count === 1 ? '.one' : '.other');
    const merged = Object.assign({ n: count }, vars || {});
    return translate(baseKey + suffix, merged);
  }

  /**
   * Traduit un message renvoyé par le serveur.
   * Le serveur envoie un `code` connu (traduisible) et/ou un texte brut.
   */
  function fromServer(payload, fallbackKey) {
    if (payload && payload.code && DICT[currentLang]['server.' + payload.code]) {
      return translate('server.' + payload.code);
    }
    if (payload && payload.error) return payload.error;
    if (payload && payload.message) return payload.message;
    return fallbackKey ? translate(fallbackKey) : '';
  }

  // ===============================================
  // APPLICATION AU DOM
  // ===============================================

  function applyDom(root) {
    const scope = root || document;

    scope.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = translate(el.getAttribute('data-i18n'));
    });

    scope.querySelectorAll('[data-i18n-html]').forEach(el => {
      el.innerHTML = translate(el.getAttribute('data-i18n-html'));
    });

    scope.querySelectorAll('[data-i18n-attr]').forEach(el => {
      el.getAttribute('data-i18n-attr').split(',').forEach(pair => {
        const parts = pair.split(':');
        if (parts.length !== 2) return;
        el.setAttribute(parts[0].trim(), translate(parts[1].trim()));
      });
    });

    document.documentElement.setAttribute('lang', currentLang);
    updateSwitchers();
  }

  // ===============================================
  // SÉLECTEUR DE LANGUE
  // ===============================================

  function buildSwitchers() {
    document.querySelectorAll('[data-i18n-switcher]').forEach(container => {
      if (container.dataset.i18nSwitcherReady === '1') return;
      container.dataset.i18nSwitcherReady = '1';
      container.classList.add('neuro_lang-switch');
      container.setAttribute('role', 'group');

      SUPPORTED.forEach(lang => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'neuro_lang-btn';
        btn.dataset.lang = lang;
        btn.textContent = lang.toUpperCase();
        btn.title = DICT[lang]['common.languageName'];
        btn.addEventListener('click', () => setLang(lang));
        container.appendChild(btn);
      });
    });
  }

  function updateSwitchers() {
    document.querySelectorAll('.neuro_lang-btn').forEach(btn => {
      const active = btn.dataset.lang === currentLang;
      btn.classList.toggle('neuro_lang-btn-active', active);
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    });

    // Sélecteurs <select data-i18n-select> (page de configuration)
    document.querySelectorAll('[data-i18n-select]').forEach(select => {
      select.value = currentLang;
    });
  }

  // ===============================================
  // CHANGEMENT DE LANGUE
  // ===============================================

  function setLang(lang, options) {
    const next = normalize(lang) || DEFAULT_LANG;
    const changed = next !== currentLang;
    currentLang = next;

    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (e) { /* stockage indisponible */ }
    writeCookie(COOKIE_KEY, next);

    applyDom();

    if (!options || options.persistServer !== false) {
      // Persiste la préférence côté serveur (best effort)
      fetch('/api/language', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: next })
      }).catch(() => { /* la préférence locale suffit */ });
    }

    if (changed) {
      listeners.forEach(fn => {
        try {
          fn(next);
        } catch (e) {
          console.error('[i18n] Erreur dans un écouteur de langue:', e);
        }
      });
    }
    return changed;
  }

  function onChange(fn) {
    if (typeof fn === 'function') listeners.push(fn);
  }

  // ===============================================
  // FORMATAGE LOCALISÉ
  // ===============================================

  function locale() {
    return LOCALES[currentLang] || LOCALES[DEFAULT_LANG];
  }

  function formatTime(value) {
    if (!value) return '--';
    try {
      return new Date(value).toLocaleTimeString(locale());
    } catch (e) {
      return '--';
    }
  }

  function formatDate(year, month, day) {
    try {
      return new Date(Number(year), Number(month) - 1, Number(day)).toLocaleDateString(locale());
    } catch (e) {
      return `${day}/${month}/${year}`;
    }
  }

  function formatNumber(value) {
    try {
      return Number(value).toLocaleString(locale());
    } catch (e) {
      return String(value);
    }
  }

  // ===============================================
  // INITIALISATION
  // ===============================================

  currentLang = detectInitialLang();
  document.documentElement.setAttribute('lang', currentLang);

  // Le HTML porte les libellés FR par défaut : on masque le contenu le temps de
  // la première traduction pour éviter un clignotement FR -> EN. L'attribut
  // n'est posé que si ce script s'exécute, donc une panne de chargement laisse
  // la page visible.
  if (currentLang !== DEFAULT_LANG) {
    document.documentElement.setAttribute('data-i18n-pending', '');
  }

  function init() {
    buildSwitchers();
    applyDom();
    document.documentElement.removeAttribute('data-i18n-pending');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  const I18n = {
    get lang() { return currentLang; },
    supported: SUPPORTED.slice(),
    defaultLang: DEFAULT_LANG,
    t: translate,
    plural,
    fromServer,
    setLang,
    onChange,
    apply: applyDom,
    locale,
    formatTime,
    formatDate,
    formatNumber
  };

  global.I18n = I18n;
  global.t = translate;
})(window);
