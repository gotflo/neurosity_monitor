/**
 * APPLICATION NEUROSITY MONITOR
 * Interface utilisateur adaptée à la détection biologique réelle
 */

// État global de l'application
window.AppState = {
    isConnected: false,
    isRecording: false,
    isMonitoring: false,
    socket: null,
    chart: null,
    deviceStatus: {
        online: false,
        battery: 'unknown',
        signal: 'disconnected',
        validation: 'pending'
    },
    connectionHealth: true,
    lastDataTime: null,
    detectionInProgress: false
};

/**
 * Initialisation au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Démarrage Neurosity Monitor');

    initializeUI();
    initializeCharts();
    initializeWebSocket();
    loadSessions();

    showToast('🧠 Application prête ! Détection activée - Allumez votre casque Neurosity Crown puis cliquez "Connecter"', 'info', 8000);
    console.log('✅ Application prête avec détection');
});

/**
 * Système de notifications Toast amélioré pour la détection
 */
function showToast(message, type = 'info', duration = 4000) {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 450px;
        `;
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        padding: 16px 22px;
        border-radius: 12px;
        color: white;
        font-weight: 500;
        font-size: 14px;
        line-height: 1.4;
        min-width: 350px;
        box-shadow: 0 6px 25px rgba(0,0,0,0.15);
        transform: translateX(100%);
        transition: transform 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    `;

    const colors = {
        success: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
        error: 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)',
        warning: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)',
        info: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        detection: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)'
    };

    toast.style.background = colors[type] || colors.info;

    // Icônes spéciales pour la détection
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: '💡',
        detection: '🔬'
    };

    const icon = icons[type] || icons.info;

    toast.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 12px;">
            <div style="font-size: 18px; margin-top: 2px;">${icon}</div>
            <div style="flex: 1; line-height: 1.4;">${message}</div>
            <div style="cursor: pointer; opacity: 0.8; font-size: 18px; margin-left: 8px;">×</div>
        </div>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 10);

    const closeBtn = toast.querySelector('div:last-child');
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        removeToast(toast);
    });

    toast.addEventListener('click', () => {
        removeToast(toast);
    });

    if (duration > 0) {
        setTimeout(() => {
            removeToast(toast);
        }, duration);
    }
}

function removeToast(toast) {
    if (toast && toast.parentNode) {
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

/**
 * Initialise l'interface utilisateur
 */
function initializeUI() {
    console.log('🎨 Initialisation UI avec détection ...');
    updateConnectionStatus(false, false, false);

    // Ajouter indicateur de détection stricte
    addStrictDetectionIndicator();
}

/**
 * Ajoute un indicateur de mode détection
 */
function addStrictDetectionIndicator() {
    const navbar = document.querySelector('.navbar');
    if (navbar && !document.getElementById('strictModeIndicator')) {
        const indicator = document.createElement('div');
        indicator.id = 'strictModeIndicator';
        indicator.style.cssText = `
            position: absolute;
            top: -8px;
            right: 20px;
            background: linear-gradient(135deg, #8b5cf6, #a855f7);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
        `;
        indicator.textContent = '🔬 Détection';
        navbar.appendChild(indicator);
    }
}

/**
 * Initialise WebSocket avec gestion des nouveaux événements de détection
 */
function initializeWebSocket() {
    console.log('🔌 Initialisation WebSocket avec détection du casque...');

    try {
        window.AppState.socket = io({
            transports: ['polling', 'websocket'],
            timeout: 30000,  // Timeout plus long pour la détection
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 2000
        });

        window.AppState.socket.on('connect', function() {
            console.log('✅ WebSocket connecté');
            showToast('🔌 Connexion WebSocket établie - Mode détection casque actif', 'success', 3000);
        });

        window.AppState.socket.on('disconnect', function() {
            console.log('❌ WebSocket déconnecté');
            showToast('🔌 Connexion WebSocket perdue', 'warning', 3000);
        });

        window.AppState.socket.on('connect_error', function(error) {
            console.error('❌ Erreur WebSocket:', error);
            showToast('❌ Erreur de connexion WebSocket', 'error');
        });

        // Données en temps réel
        window.AppState.socket.on('calm_data', handleCalmData);
        window.AppState.socket.on('focus_data', handleFocusData);
        window.AppState.socket.on('brainwaves_data', handleBrainwavesData);

        // Messages de statut
        window.AppState.socket.on('status', function(data) {
            updateConnectionStatus(data.connected, data.recording, data.monitoring);
            if (data.device_status) {
                updateDeviceStatus(data.device_status);
            }
        });

        window.AppState.socket.on('status_update', function(data) {
            updateConnectionStatus(data.connected, false, data.monitoring);
            updateDeviceStatus(data.device_status);
        });

        window.AppState.socket.on('error', function(data) {
            showToast('❌ ' + (data.message || 'Erreur WebSocket'), 'error');
        });

        window.AppState.socket.on('monitoring_started', function() {
            showToast('🎯 Monitoring démarré ! Données biologiques validées en temps réel', 'success');
            window.AppState.isMonitoring = true;
            updateMonitoringStatus(true);
        });

        window.AppState.socket.on('monitoring_stopped', function() {
            showToast('⏹️ Monitoring arrêté', 'info');
            window.AppState.isMonitoring = false;
            updateMonitoringStatus(false);
        });

        // Événements de surveillance de connexion
        window.AppState.socket.on('connection_warning', function(data) {
            showToast(`⚠️ ${data.message}`, 'warning', 8000);
            window.AppState.connectionHealth = false;
            updateConnectionHealth(false);
        });

        window.AppState.socket.on('connection_restored', function(data) {
            showToast(`✅ ${data.message}`, 'success', 3000);
            window.AppState.connectionHealth = true;
            updateConnectionHealth(true);
        });

        window.AppState.socket.on('device_status_response', function(data) {
            console.log('Statut dispositif:', data);
            if (data.device_status) {
                updateDeviceStatus(data.device_status);
            }
        });

    } catch (error) {
        console.error('❌ Erreur WebSocket:', error);
        showToast('❌ Erreur de connexion WebSocket', 'error');
    }
}

/**
 * Connecte le casque avec interface de détection stricte
 */
async function connectDevice() {
    const connectBtn = document.getElementById('connectBtn');

    console.log('🔗 Tentative de connexion avec détection du crown...');

    // Interface de détection en cours
    showDetectionProgress();

    try {
        connectBtn.disabled = true;
        connectBtn.innerHTML = '<span>🔬</span><span class="btn-text"> Détection...</span>';
        window.AppState.detectionInProgress = true;

        showToast('🔬 Démarrage de la détection du casque Neurosity Crown...', 'detection', 0);

        const response = await fetch('/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (result.success) {
            window.AppState.isConnected = true;
            window.AppState.deviceStatus = result.device_status || {};

            console.log('✅ Casque connecté avec validation  !', result);

            // Message de succès détaillé
            const validationInfo = result.device_status?.validation || 'Données biologiques confirmées';
            const dataPoints = result.device_status?.data_points || 'N/A';

            showToast(`✅ Casque Neurosity Crown validé ! ${validationInfo} (${dataPoints} points analysés)`, 'success', 6000);

            updateDeviceStatus(window.AppState.deviceStatus);
            hideDetectionProgress();

            // Démarrer automatiquement le monitoring
            setTimeout(() => {
                startMonitoring();
            }, 1000);
        } else {
            console.error('❌ Échec de détection :', result);

            // Messages d'erreur spécifiques
            const errorMsg = result.error || 'Erreur de connexion inconnue';
            const helpMsg = result.help || '';

            hideDetectionProgress();

            if (errorMsg.includes('NON DÉTECTÉ')) {
                showToast(`❌ Casque non détecté ! ${errorMsg}`, 'error', 10000);
                if (helpMsg) {
                    setTimeout(() => {
                        showToast(`💡 ${helpMsg}`, 'info', 8000);
                    }, 2000);
                }
            } else {
                showToast(`❌ ${errorMsg}`, 'error', 6000);
            }
        }

    } catch (error) {
        console.error('❌ Erreur de connexion:', error);
        showToast('❌ Erreur de connexion : ' + error.message, 'error');
        hideDetectionProgress();
    } finally {
        window.AppState.detectionInProgress = false;
        updateConnectionStatus(window.AppState.isConnected, window.AppState.isRecording, window.AppState.isMonitoring);
    }
}

/**
 * Affiche l'interface de progression de détection
 */
function showDetectionProgress() {
    // Supprimer l'interface précédente si elle existe
    hideDetectionProgress();

    const progressOverlay = document.createElement('div');
    progressOverlay.id = 'detectionProgress';
    progressOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(5px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.3s ease;
    `;

    progressOverlay.innerHTML = `
        <div style="
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            padding: 40px;
            border-radius: 20px;
            color: white;
            text-align: center;
            max-width: 500px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        ">
            <div style="font-size: 3rem; margin-bottom: 20px;">🔬</div>
            <h3 style="margin: 0 0 10px 0; font-size: 1.5rem;">Détection en Cours</h3>
            <p style="margin: 0 0 20px 0; opacity: 0.9; line-height: 1.5;">
                Analyse des données biologiques de votre casque Neurosity Crown...<br>
                <strong>Veuillez patienter jusqu'à 20 secondes</strong>
            </p>
            <div style="
                width: 100%;
                height: 6px;
                background: rgba(255,255,255,0.2);
                border-radius: 3px;
                overflow: hidden;
                margin-bottom: 15px;
            ">
                <div id="detectionProgressBar" style="
                    width: 0%;
                    height: 100%;
                    background: linear-gradient(90deg, #ffffff, #f1f5f9);
                    border-radius: 3px;
                    transition: width 0.3s ease;
                "></div>
            </div>
            <div id="detectionStatus" style="font-size: 0.9rem; opacity: 0.8;">
                Initialisation de la détection...
            </div>
        </div>
    `;

    document.body.appendChild(progressOverlay);

    // Animation de la barre de progression
    animateDetectionProgress();
}

/**
 * Anime la barre de progression de détection
 */
function animateDetectionProgress() {
    const progressBar = document.getElementById('detectionProgressBar');
    const statusText = document.getElementById('detectionStatus');

    if (!progressBar || !statusText) return;

    const steps = [
        { progress: 10, status: 'Connexion au SDK Neurosity...', time: 1000 },
        { progress: 25, status: 'Authentification en cours...', time: 2000 },
        { progress: 40, status: 'Recherche du casque...', time: 3000 },
        { progress: 55, status: 'Collecte des données biologiques...', time: 8000 },
        { progress: 75, status: 'Validation des patterns naturels...', time: 4000 },
        { progress: 90, status: 'Analyse de cohérence temporelle...', time: 2000 },
        { progress: 100, status: 'Validation finale...', time: 1000 }
    ];

    let currentStep = 0;

    function updateStep() {
        if (currentStep < steps.length && document.getElementById('detectionProgress')) {
            const step = steps[currentStep];
            progressBar.style.width = step.progress + '%';
            statusText.textContent = step.status;
            currentStep++;

            setTimeout(updateStep, step.time);
        }
    }

    updateStep();
}

/**
 * Cache l'interface de progression de détection
 */
function hideDetectionProgress() {
    const progressOverlay = document.getElementById('detectionProgress');
    if (progressOverlay) {
        progressOverlay.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            if (progressOverlay.parentNode) {
                progressOverlay.parentNode.removeChild(progressOverlay);
            }
        }, 300);
    }
}

/**
 * Met à jour le statut du dispositif avec informations de validation
 */
function updateDeviceStatus(deviceStatus) {
    window.AppState.deviceStatus = deviceStatus;

    const deviceIndicator = document.getElementById('deviceStatusIndicator');
    const deviceDot = document.getElementById('deviceStatusDot');
    const deviceText = document.getElementById('deviceStatusText');

    if (deviceIndicator && deviceDot && deviceText) {
        if (deviceStatus.online) {
            deviceIndicator.style.display = 'flex';
            deviceDot.className = 'status-dot status-connected';

            // Information enrichie avec validation
            let statusText = 'Crown';

            if (deviceStatus.validation === 'biological_data_confirmed') {
                statusText += ' ✓';
            }

            if (deviceStatus.battery && deviceStatus.battery !== 'unknown') {
                statusText += ` ${deviceStatus.battery}%`;
            }

            if (deviceStatus.signal && deviceStatus.signal !== 'unknown') {
                const signalEmoji = {
                    'excellent': '🟢',
                    'good': '🟡',
                    'poor': '🟠',
                    'biological_data_confirmed': '🔬'
                }[deviceStatus.signal] || '🔴';
                statusText += ` ${signalEmoji}`;
            }

            deviceText.textContent = statusText;
        } else {
            deviceIndicator.style.display = 'none';
        }
    }

    // Mettre à jour le statut système si la fonction existe
    if (typeof updateSystemStatus === 'function') {
        updateSystemStatus(window.AppState.isConnected, window.AppState.isMonitoring, deviceStatus);
    }
}

/**
 * Met à jour l'indicateur de santé de connexion
 */
function updateConnectionHealth(healthy) {
    const connectionStatus = document.getElementById('connectionStatus');
    if (connectionStatus && window.AppState.isConnected) {
        if (healthy) {
            connectionStatus.className = 'status-dot status-connected';
        } else {
            connectionStatus.className = 'status-dot status-recording'; // Orange pour warning
        }
    }
}

/**
 * Met à jour le statut de monitoring
 */
function updateMonitoringStatus(monitoring) {
    const charts = document.querySelectorAll('.chart-card');
    charts.forEach(chart => {
        if (monitoring) {
            chart.style.borderLeft = '4px solid #10b981';
            chart.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.1)';
        } else {
            chart.style.borderLeft = 'none';
            chart.style.boxShadow = '';
        }
    });
}

/**
 * Initialise les graphiques (identique)
 */
function initializeCharts() {
    console.log('📊 Initialisation des graphiques...');

    const canvas = document.getElementById('brainwavesChart');
    if (!canvas) {
        console.error('❌ Canvas non trouvé');
        return;
    }

    if (window.AppState.chart) {
        window.AppState.chart.destroy();
    }

    const ctx = canvas.getContext('2d');

    window.AppState.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Delta (0.5-4 Hz)',
                    data: [],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderWidth: 2
                },
                {
                    label: 'Theta (4-8 Hz)',
                    data: [],
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderWidth: 2
                },
                {
                    label: 'Alpha (8-12 Hz)',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderWidth: 2
                },
                {
                    label: 'Beta (12-30 Hz)',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderWidth: 2
                },
                {
                    label: 'Gamma (30+ Hz)',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            family: 'Inter',
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Ondes Cérébrales Validées',
                    font: {
                        family: 'Inter',
                        size: 14,
                        weight: '600'
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Temps',
                        font: {
                            family: 'Inter',
                            size: 12,
                            weight: '500'
                        },
                        color: '#64748b'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: '#94a3b8',
                        maxTicksLimit: 10
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Amplitude (μV) - Données Biologiques',
                        font: {
                            family: 'Inter',
                            size: 12,
                            weight: '500'
                        },
                        color: '#64748b'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: '#94a3b8'
                    },
                    beginAtZero: true
                }
            }
        }
    });

    console.log('✅ Graphiques créés avec validation');
}

/**
 * Démarre le monitoring automatiquement
 */
function startMonitoring() {
    if (window.AppState.socket && window.AppState.isConnected) {
        console.log('🎯 Démarrage automatique du monitoring...');
        window.AppState.socket.emit('start_monitoring');
    }
}

/**
 * Gère l'enregistrement (identique)
 */
async function toggleRecording() {
    if (!window.AppState.isConnected) {
        showToast('⚠️ Connectez d\'abord votre casque Neurosity Crown avec la détection', 'warning');
        return;
    }

    try {
        const endpoint = window.AppState.isRecording ? '/stop_recording' : '/start_recording';
        const actionText = window.AppState.isRecording ? 'Arrêt' : 'Démarrage';

        showToast(`🎬 ${actionText} de l'enregistrement...`, 'info');

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (result.success) {
            window.AppState.isRecording = result.recording;

            if (window.AppState.isRecording) {
                showToast('🔴 Enregistrement démarré ! Données biologiques validées sauvegardées en temps réel', 'success');
            } else {
                showToast('⏹️ Enregistrement arrêté. Fichier CSV avec données validées disponible', 'success');
                setTimeout(loadSessions, 1000);
            }
        }

        updateConnectionStatus(window.AppState.isConnected, window.AppState.isRecording, window.AppState.isMonitoring);

    } catch (error) {
        console.error('❌ Erreur enregistrement:', error);
        showToast('❌ Erreur d\'enregistrement: ' + error.message, 'error');
    }
}

/**
 * Télécharge les données (identique)
 */
async function downloadData() {
    try {
        showToast('📥 Recherche de la dernière session validée...', 'info');

        const response = await fetch('/sessions');
        const data = await response.json();

        if (data.sessions && data.sessions.length > 0) {
            const latestSession = data.sessions[0];
            const link = document.createElement('a');
            link.href = `/download/${latestSession}`;
            link.download = latestSession;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            showToast(`📊 Téléchargement de ${latestSession} (données biologiques validées)`, 'success');
        } else {
            showToast('📝 Aucune session disponible. Démarrez un enregistrement d\'abord.', 'warning');
        }
    } catch (error) {
        console.error('❌ Erreur téléchargement:', error);
        showToast('❌ Erreur de téléchargement: ' + error.message, 'error');
    }
}

/**
 * Met à jour l'interface utilisateur
 */
function updateConnectionStatus(connected, recording, monitoring) {
    window.AppState.isConnected = connected;
    window.AppState.isRecording = recording;
    window.AppState.isMonitoring = monitoring;

    const connectBtn = document.getElementById('connectBtn');
    const recordBtn = document.getElementById('recordBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const connectionStatus = document.getElementById('connectionStatus');
    const connectionText = document.getElementById('connectionText');
    const recordingStatus = document.getElementById('recordingStatus');

    if (connectBtn) {
        if (connected) {
            connectionStatus.className = 'status-dot status-connected';
            connectionText.textContent = 'Connecté (Validé)';
            connectBtn.innerHTML = '<span>✅</span><span class="btn-text"> Validé</span>';
            connectBtn.disabled = true;
            connectBtn.className = 'btn btn-success';
        } else {
            connectionStatus.className = 'status-dot status-disconnected';
            connectionText.textContent = 'Déconnecté';
            connectBtn.innerHTML = '<span>🔬</span><span class="btn-text"> Connecter</span>';
            connectBtn.disabled = window.AppState.detectionInProgress;
            connectBtn.className = 'btn btn-primary';
        }
    }

    if (recordBtn) {
        recordBtn.disabled = !connected;

        if (recording) {
            recordBtn.innerHTML = '<span>⏹️</span><span class="btn-text"> Arrêter</span>';
            recordBtn.className = 'btn btn-danger';
        } else {
            recordBtn.innerHTML = '<span>⏺️</span><span class="btn-text"> Enregistrer</span>';
            recordBtn.className = 'btn btn-success';
        }
    }

    if (downloadBtn) {
        downloadBtn.disabled = !connected;
    }

    if (recordingStatus) {
        if (recording) {
            recordingStatus.style.display = 'flex';
        } else {
            recordingStatus.style.display = 'none';
        }
    }
}

/**
 * Gestionnaires des données en temps réel (identiques)
 */
function handleCalmData(data) {
    if (!window.AppState.isConnected) return;

    window.AppState.lastDataTime = new Date();
    updateCircularProgress('calm', data.calm, data.timestamp);
    flashDataIndicator('calm');
}

function handleFocusData(data) {
    if (!window.AppState.isConnected) return;

    window.AppState.lastDataTime = new Date();
    updateCircularProgress('focus', data.focus, data.timestamp);
    flashDataIndicator('focus');
}

function handleBrainwavesData(data) {
    if (!window.AppState.isConnected || !window.AppState.chart) return;

    window.AppState.lastDataTime = new Date();

    const time = formatTime(data.timestamp);
    const chart = window.AppState.chart;

    const avgData = {
        delta: calculateAverage(data.delta),
        theta: calculateAverage(data.theta),
        alpha: calculateAverage(data.alpha),
        beta: calculateAverage(data.beta),
        gamma: calculateAverage(data.gamma)
    };

    chart.data.labels.push(time);
    chart.data.datasets[0].data.push(avgData.delta);
    chart.data.datasets[1].data.push(avgData.theta);
    chart.data.datasets[2].data.push(avgData.alpha);
    chart.data.datasets[3].data.push(avgData.beta);
    chart.data.datasets[4].data.push(avgData.gamma);

    if (chart.data.labels.length > 50) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => dataset.data.shift());
    }

    chart.update('none');

    const timestampElement = document.getElementById('brainwavesTimestamp');
    if (timestampElement) {
        timestampElement.textContent = 'Dernière validation: ' + formatTimestamp(data.timestamp);
    }

    flashDataIndicator('brainwaves');
}

/**
 * Indicateur visuel de réception de données
 */
function flashDataIndicator(type) {
    const elements = {
        'calm': document.querySelector('.metric-card:nth-child(1)'),
        'focus': document.querySelector('.metric-card:nth-child(2)'),
        'brainwaves': document.querySelector('.chart-card')
    };

    const element = elements[type];
    if (element) {
        element.style.boxShadow = '0 0 20px rgba(139, 92, 246, 0.4)';
        setTimeout(() => {
            element.style.boxShadow = '';
        }, 300);
    }
}

/**
 * Met à jour les indicateurs circulaires
 */
function updateCircularProgress(type, value, timestamp) {
    const circumference = 2 * Math.PI * 65;
    const progress = Math.min(Math.max(value, 0), 100);
    const offset = circumference - (progress / 100) * circumference;

    const progressElement = document.getElementById(`${type}Progress`);
    const valueElement = document.getElementById(`${type}Value`);
    const timestampElement = document.getElementById(`${type}Timestamp`);

    if (progressElement) {
        progressElement.style.strokeDasharray = circumference;
        progressElement.style.strokeDashoffset = offset;
    }

    if (valueElement) {
        valueElement.textContent = Math.round(progress) + '%';
    }

    if (timestampElement) {
        timestampElement.textContent = formatTimestamp(timestamp) + ' ✓';
    }
}

/**
 * Charge la liste des sessions
 */
async function loadSessions() {
    try {
        const response = await fetch('/sessions');
        const data = await response.json();
        displaySessions(data.sessions || []);
        return Promise.resolve();
    } catch (error) {
        console.error('❌ Erreur chargement sessions:', error);
        const sessionsList = document.getElementById('sessionsList');
        if (sessionsList) {
            sessionsList.innerHTML = '<p style="color: #ef4444;">Erreur de chargement des sessions</p>';
        }
        return Promise.reject(error);
    }
}

/**
 * Affiche les sessions avec indication de validation
 */
function displaySessions(sessions) {
    const sessionsList = document.getElementById('sessionsList');
    if (!sessionsList) return;

    if (sessions.length === 0) {
        sessionsList.innerHTML = `
            <div class="sessions-empty">
                Aucune session validée enregistrée
                <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.7;">
                    Connectez votre casque avec détection pour créer une session
                </div>
            </div>
        `;
        sessionsList.className = 'sessions-empty';
        return;
    }

    sessionsList.className = '';
    sessionsList.innerHTML = '';

    sessions.forEach((session, index) => {
        const sessionItem = document.createElement('div');
        sessionItem.className = 'session-item';
        sessionItem.style.animationDelay = `${index * 0.1}s`;

        const dateMatch = session.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
        let displayDate = 'Session';
        if (dateMatch) {
            const [, year, month, day, hour, minute, second] = dateMatch;
            displayDate = `${day}/${month}/${year} ${hour}:${minute}`;
        }

        sessionItem.innerHTML = `
            <div class="session-info">
                <div class="session-name">${session} <span style="color: #8b5cf6;">✓</span></div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.25rem;">
                    📅 ${displayDate} • Données biologiques validées
                </div>
            </div>
            <div class="session-actions">
                <button class="btn btn-outline btn-small" onclick="downloadSession('${session}')" title="Télécharger CSV validé">
                    <span>⬇️</span> CSV
                </button>
            </div>
        `;
        sessionsList.appendChild(sessionItem);
    });

    if (sessions.length > 0) {
        showToast(`📁 ${sessions.length} session(s) validée(s) trouvée(s)`, 'info', 2000);
    }
}

/**
 * Fonction pour le statut système
 */
function updateSystemStatus(connected, monitoring, deviceStatus) {
    const elements = {
        connection: document.getElementById('systemConnectionStatus'),
        monitoring: document.getElementById('systemMonitoringStatus'),
        signal: document.getElementById('systemSignalQuality'),
        battery: document.getElementById('systemBattery')
    };

    if (!elements.connection) return;

    Object.values(elements).forEach(el => {
        if (el) {
            el.style.transform = 'scale(0.95)';
            el.style.opacity = '0.7';
        }
    });

    setTimeout(() => {
        if (elements.connection) {
            elements.connection.textContent = connected ? '✅ Connecté (Validé)' : '❌ Déconnecté';
            elements.connection.style.background = connected ?
                'rgba(139, 92, 246, 0.1)' : 'rgba(239, 68, 68, 0.1)';
            elements.connection.style.color = connected ? '#8b5cf6' : '#dc2626';
            elements.connection.style.borderColor = connected ?
                'rgba(139, 92, 246, 0.3)' : 'rgba(239, 68, 68, 0.3)';
        }

        if (elements.monitoring) {
            elements.monitoring.textContent = monitoring ? '🎯 Actif (Validé)' : '⏹️ Arrêté';
            elements.monitoring.style.background = monitoring ?
                'rgba(139, 92, 246, 0.1)' : 'rgba(148, 163, 184, 0.1)';
            elements.monitoring.style.color = monitoring ? '#8b5cf6' : '#64748b';
            elements.monitoring.style.borderColor = monitoring ?
                'rgba(139, 92, 246, 0.3)' : 'rgba(148, 163, 184, 0.3)';
        }

        if (elements.signal && deviceStatus) {
            const signal = deviceStatus.signal || 'unknown';
            const validation = deviceStatus.validation || '';

            let signalText = 'Inconnu';
            let signalColor = '#dc2626';
            let signalBg = 'rgba(239, 68, 68, 0.1)';
            let signalEmoji = '🔴';

            if (validation === 'biological_data_confirmed') {
                signalText = 'Données Biologiques ✓';
                signalColor = '#8b5cf6';
                signalBg = 'rgba(139, 92, 246, 0.1)';
                signalEmoji = '🔬';
            } else if (signal === 'excellent') {
                signalText = 'Excellent';
                signalColor = '#059669';
                signalBg = 'rgba(16, 185, 129, 0.1)';
                signalEmoji = '🟢';
            }

            elements.signal.textContent = `${signalEmoji} ${signalText}`;
            elements.signal.style.background = signalBg;
            elements.signal.style.color = signalColor;
            elements.signal.style.borderColor = signalColor + '40';
        }

        if (elements.battery && deviceStatus) {
            const battery = deviceStatus.battery || 0;
            let batteryConfig;

            if (battery > 60 || battery === 'unknown') {
                batteryConfig = { emoji: '🔋', color: '#059669', bg: 'rgba(16, 185, 129, 0.1)' };
            } else if (battery > 30) {
                batteryConfig = { emoji: '🪫', color: '#d97706', bg: 'rgba(245, 158, 11, 0.1)' };
            } else if (battery > 0) {
                batteryConfig = { emoji: '🔴', color: '#dc2626', bg: 'rgba(239, 68, 68, 0.1)' };
            } else {
                batteryConfig = { emoji: '❓', color: '#64748b', bg: 'rgba(148, 163, 184, 0.1)' };
            }

            const batteryText = battery === 'unknown' ? 'N/A' : `${battery}%`;
            elements.battery.textContent = `${batteryConfig.emoji} ${batteryText}`;
            elements.battery.style.background = batteryConfig.bg;
            elements.battery.style.color = batteryConfig.color;
            elements.battery.style.borderColor = batteryConfig.color + '40';
        }

        Object.values(elements).forEach(el => {
            if (el) {
                el.style.transform = 'scale(1)';
                el.style.opacity = '1';
                el.style.transition = 'all 0.3s ease';
            }
        });
    }, 150);
}

function downloadSession(filename) {
    const link = document.createElement('a');
    link.href = `/download/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast(`📊 Téléchargement de ${filename} (données validées)`, 'success');
}

function checkDeviceStatus() {
    if (window.AppState.socket && window.AppState.isConnected) {
        window.AppState.socket.emit('check_device_status');
    }
}

setInterval(checkDeviceStatus, 30000);

/**
 * Fonctions utilitaires
 */
function calculateAverage(array) {
    if (!array || array.length === 0) return 0;
    const validNumbers = array.filter(val => typeof val === 'number' && !isNaN(val));
    if (validNumbers.length === 0) return 0;
    return validNumbers.reduce((a, b) => a + b, 0) / validNumbers.length;
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '--';
    try {
        return new Date(timestamp).toLocaleString('fr-FR');
    } catch {
        return '--';
    }
}

function formatTime(timestamp) {
    if (!timestamp) return '--';
    try {
        return new Date(timestamp).toLocaleTimeString('fr-FR');
    } catch {
        return '--';
    }
}

// Compatibilité
function showMessage(message, type) {
    showToast(message, type);
}

// Styles CSS pour les animations
const detectionStyles = document.createElement('style');
detectionStyles.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
    
    #strictModeIndicator {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
`;
document.head.appendChild(detectionStyles);

// Gestion des erreurs globales
window.addEventListener('error', function(event) {
    console.error('Erreur JavaScript:', event.error);
    showToast('❌ Erreur application: ' + event.error.message, 'error');
});

window.addEventListener('beforeunload', function(event) {
    if (window.AppState.isRecording) {
        event.preventDefault();
        event.returnValue = 'Un enregistrement de données biologiques validées est en cours. Êtes-vous sûr de vouloir fermer ?';
        return event.returnValue;
    }
});

// Exporter les fonctions principales
window.connectDevice = connectDevice;
window.toggleRecording = toggleRecording;
window.downloadData = downloadData;
window.loadSessions = loadSessions;
window.displaySessions = displaySessions;
window.updateSystemStatus = updateSystemStatus;
window.showToast = showToast;

console.log('✅ Application Neurosity Monitor');