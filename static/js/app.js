/**
 * NEUROSITY MONITOR - APPLICATION JAVASCRIPT OPTIMISÉE
 */

// ===============================================
// CONFIGURATION ET ÉTAT GLOBAL
// ===============================================

const NeuroApp = {
  state: {
    isConnected: false,
    isRecording: false,
    isMonitoring: false,
    deviceStatus: {
      online: false,
      battery: 'unknown',
      charging: false,
      signal: 'disconnected'
    },
    sessions: [],
    charts: {
      brainwaves: null,
      eegRaw: null
    }
  },
  config: {
    toastDuration: 4000,
    chartUpdateAnimation: 100
  }
};

// ===============================================
// GESTIONNAIRE DE WEBSOCKET
// ===============================================

const SocketManager = {
  socket: null,

  init() {
    console.log('Initialisation WebSocket...');

    this.socket = io({
      transports: ['polling', 'websocket'],
      timeout: 30000,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 2000
    });

    this.setupEventHandlers();
  },

  setupEventHandlers() {
    // Connexion
    this.socket.on('connect', () => {
      console.log('WebSocket connecté');
      UI.showToast(t('toast.ws.connected'), 'success', 3000);
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket déconnecté');
      UI.showToast(t('toast.ws.lost'), 'warning', 3000);
    });

    // Données temps réel
    this.socket.on('calm_data', (data) => DataHandler.handleMetricData('calm', data));
    this.socket.on('focus_data', (data) => DataHandler.handleMetricData('focus', data));
    this.socket.on('brainwaves_data', (data) => DataHandler.handleBrainwavesData(data));
    this.socket.on('signal_quality_data', (data) => DataHandler.handleSignalQualityData(data));
    this.socket.on('brainwaves_raw_data', (data) => DataHandler.handleBrainwavesRawData(data));
    this.socket.on('battery_data', (data) => UI.updateBatteryStatus(data));

    // Statuts
    this.socket.on('status', (data) => {
      UI.updateConnectionStatus(data.connected, data.recording, data.monitoring);
      if (data.device_status) {
        UI.updateDeviceStatus(data.device_status);
      }
    });

    this.socket.on('monitoring_started', () => {
      UI.showToast(t('toast.monitoring.started'), 'success');
      NeuroApp.state.isMonitoring = true;
      UI.updateMonitoringStatus(true);
    });

    this.socket.on('monitoring_stopped', () => {
      UI.showToast(t('toast.monitoring.stopped'), 'info');
      NeuroApp.state.isMonitoring = false;
      UI.updateMonitoringStatus(false);
    });

    // Erreurs
    this.socket.on('error', (data) => {
      UI.showToast(t('toast.error', { message: I18n.fromServer(data, 'toast.unknownError') }), 'error');
    });
  },

  emit(event, data) {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('Socket non connecté');
    }
  }
};

// ===============================================
// GESTIONNAIRE DE DONNÉES
// ===============================================

const DataHandler = {
  handleMetricData(type, data) {
    if (!NeuroApp.state.isConnected) return;

    UI.updateCircularProgress(type, data[type], data.timestamp);
    UI.flashIndicator(type);
  },

  handleBrainwavesData(data) {
    if (!NeuroApp.state.isConnected || !NeuroApp.state.charts.brainwaves) return;

    // CORRECTION: Calculer la moyenne des 8 valeurs (une par électrode) pour chaque bande
    const powerData = ['delta', 'theta', 'alpha', 'beta', 'gamma'].map(wave => {
      if (data[wave] && Array.isArray(data[wave]) && data[wave].length === 8) {
        // Calculer la moyenne des 8 électrodes
        const sum = data[wave].reduce((acc, val) => acc + val, 0);
        const average = sum / data[wave].length;
        return Math.min(average, 20); // Limiter à 20 pour l'échelle du graphique
      } else {
        // Ancien format ou erreur - traiter comme une valeur unique
        return Math.min(data[wave] || 0, 20);
      }
    });

    // Mettre à jour le graphique
    NeuroApp.state.charts.brainwaves.data.datasets[0].data = powerData;
    NeuroApp.state.charts.brainwaves.update('none');

    // Mettre à jour le timestamp
    UI.updateLastUpdate('brainwavesTimestamp', data.timestamp);

    // Effet visuel
    UI.flashIndicator('brainwaves');

    // Debug optionnel (visible dans la console du navigateur)
    console.debug('🧠 Brainwaves:', {
      delta: data.delta ? `${data.delta.length} valeurs` : 'absent',
      theta: data.theta ? `${data.theta.length} valeurs` : 'absent',
      alpha: data.alpha ? `${data.alpha.length} valeurs` : 'absent',
      beta: data.beta ? `${data.beta.length} valeurs` : 'absent',
      gamma: data.gamma ? `${data.gamma.length} valeurs` : 'absent',
      moyennes_affichées: powerData
    });
  },

handleSignalQualityData(data) {
    if (!NeuroApp.state.isConnected) return;

    // Log pour voir les données reçues
    console.debug('📡 Signal Quality reçu:', data);

    // Liste des électrodes
    const electrodes = ['F5', 'F6', 'C3', 'C4', 'CP3', 'CP4', 'PO3', 'PO4'];

    electrodes.forEach(electrode => {
      if (data[electrode] !== undefined) {
        UI.updateElectrodeQuality(electrode, data[electrode]);
      } else {
        console.warn(`Électrode ${electrode} manquante dans les données`);
      }
    });

    UI.flashIndicator('signal_quality');
  },

  handleBrainwavesRawData(data) {
    if (!NeuroApp.state.isConnected || !NeuroApp.state.charts.eegRaw) return;

    NeuroApp.state.charts.eegRaw.updateData(data.raw_data, data.info);

    UI.updateLastUpdate('eegRawTimestamp', data.timestamp);

    UI.flashIndicator('eeg_raw');
  }
};

// ===============================================
// CLASSE POUR LE GRAPHIQUE EEG RAW
// ===============================================

class EEGRawChart {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.channelNames = ['CP3', 'C3', 'F5', 'PO3', 'PO4', 'F6', 'C4', 'CP4'];
    this.colors = [
      '#6366f1', '#0ea5e9', '#8b5cf6', '#a855f7',
      '#f59e0b', '#06b6d4', '#3b82f6', '#1e293b'
    ];

    this.dataBuffer = [];
    this.timeBuffer = [];
    this.maxBufferSize = 256 * 4; // 4 secondes à 256Hz

    this.amplitudeScale = 2;
    this.margins = {
      left: 60,
      right: 50,
      top: 30,
      bottom: 40
    };

    this.gridColor = 'rgba(226, 232, 240, 0.5)';
    this.gridTextColor = '#94a3b8';

    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = rect.width * window.devicePixelRatio;
    this.canvas.height = rect.height * window.devicePixelRatio;
    this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    this.width = rect.width;
    this.height = rect.height;
    this.plotWidth = this.width - this.margins.left - this.margins.right;
    this.plotHeight = this.height - this.margins.top - this.margins.bottom;

    this.draw();
  }

  updateData(rawData, info) {
    if (rawData && rawData.length === 8) {
      const timestamp = Date.now();
      const numSamples = rawData[0].length;

      for (let i = 0; i < numSamples; i++) {
        const sample = rawData.map(ch => ch[i]);
        this.dataBuffer.push(sample);
        this.timeBuffer.push(timestamp + (i * 1000 / 256));
      }

      if (this.dataBuffer.length > this.maxBufferSize) {
        const excess = this.dataBuffer.length - this.maxBufferSize;
        this.dataBuffer = this.dataBuffer.slice(excess);
        this.timeBuffer = this.timeBuffer.slice(excess);
      }

      this.draw();
    }
  }

  draw() {
    this.ctx.clearRect(0, 0, this.width, this.height);
    this.drawGrid();
    this.drawChannelLabels();
    this.drawTimeScale();

    if (this.dataBuffer.length > 1) {
      this.drawSignals();
    }
  }

  drawGrid() {
    this.ctx.strokeStyle = this.gridColor;
    this.ctx.lineWidth = 1;

    // Grilles horizontales et verticales
    for (let ch = 0; ch < 8; ch++) {
      const yBase = this.margins.top + (ch + 0.5) * (this.plotHeight / 8);
      this.ctx.beginPath();
      this.ctx.moveTo(this.margins.left, yBase);
      this.ctx.lineTo(this.width - this.margins.right, yBase);
      this.ctx.stroke();
    }

    // Grille verticale (secondes)
    const gridSpacing = this.plotWidth / 4;
    for (let i = 0; i <= 4; i++) {
      const x = this.margins.left + i * gridSpacing;
      this.ctx.beginPath();
      this.ctx.moveTo(x, this.margins.top);
      this.ctx.lineTo(x, this.height - this.margins.bottom);
      this.ctx.stroke();
    }

    // Cadre
    this.ctx.strokeRect(this.margins.left, this.margins.top, this.plotWidth, this.plotHeight);
  }

  drawChannelLabels() {
    this.ctx.font = '12px Inter';
    this.ctx.textAlign = 'right';
    this.ctx.textBaseline = 'middle';

    for (let ch = 0; ch < 8; ch++) {
      const yBase = this.margins.top + (ch + 0.5) * (this.plotHeight / 8);
      this.ctx.fillStyle = this.colors[ch];
      this.ctx.fillText(this.channelNames[ch], this.margins.left - 10, yBase);
    }
  }

  drawTimeScale() {
    this.ctx.font = '11px Inter';
    this.ctx.fillStyle = this.gridTextColor;
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'top';

    for (let i = 0; i <= 4; i++) {
      const x = this.margins.left + i * (this.plotWidth / 4);
      this.ctx.fillText(`-${4 - i}s`, x, this.height - this.margins.bottom + 10);
    }
  }

  drawSignals() {
    const pixelsPerSample = this.plotWidth / this.dataBuffer.length;

    for (let ch = 0; ch < 8; ch++) {
      const yBase = this.margins.top + (ch + 0.5) * (this.plotHeight / 8);

      this.ctx.save();
      this.ctx.beginPath();
      this.ctx.rect(
        this.margins.left,
        this.margins.top + ch * (this.plotHeight / 8),
        this.plotWidth,
        this.plotHeight / 8
      );
      this.ctx.clip();

      this.ctx.strokeStyle = this.colors[ch];
      this.ctx.lineWidth = 1.5;
      this.ctx.beginPath();

      for (let i = 0; i < this.dataBuffer.length; i++) {
        const x = this.margins.left + i * pixelsPerSample;
        const y = yBase - (this.dataBuffer[i][ch] * this.amplitudeScale);

        if (i === 0) {
          this.ctx.moveTo(x, y);
        } else {
          this.ctx.lineTo(x, y);
        }
      }

      this.ctx.stroke();
      this.ctx.restore();
    }
  }
}

// ===============================================
// GESTIONNAIRE D'INTERFACE (UI)
// ===============================================

const UI = {
  /**
   * Fabrique un fragment traduisible : le texte est rendu tout de suite et
   * l'attribut data-i18n permet de le retraduire au changement de langue.
   */
  i18nSpan(key, className = '') {
    const cls = className ? ` class="${className}"` : '';
    return `<span${cls} data-i18n="${key}">${t(key)}</span>`;
  },

  /**
   * Met à jour un horodatage « Dernière mise à jour » de façon traduisible.
   * La date brute est conservée pour pouvoir reformater au changement de langue.
   */
  updateLastUpdate(elementId, timestamp) {
    const el = document.getElementById(elementId);
    if (!el) return;

    if (timestamp) el.dataset.timestamp = timestamp;
    const raw = el.dataset.timestamp;
    if (!raw) return;

    el.textContent = t('chart.lastUpdate', { value: I18n.formatTime(raw) });
  },

  showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-width: 450px;
      `;
      document.body.appendChild(container);
    }

    const colors = {
      success: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
      error: 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)',
      warning: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)',
      info: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'
    };

    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: '💡'
    };

    const toast = document.createElement('div');
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
      backdrop-filter: blur(10px);
      background: ${colors[type] || colors.info};
    `;

    toast.innerHTML = `
      <div style="display: flex; align-items: flex-start; gap: 12px;">
        <div style="font-size: 18px;">${icons[type] || icons.info}</div>
        <div style="flex: 1;">${message}</div>
        <div style="cursor: pointer; opacity: 0.8;" onclick="this.parentElement.parentElement.remove()">×</div>
      </div>
    `;

    container.appendChild(toast);
    setTimeout(() => toast.style.transform = 'translateX(0)', 10);

    if (duration > 0) {
      setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
      }, duration);
    }
  },

  updateConnectionStatus(connected, recording, monitoring) {
    NeuroApp.state.isConnected = connected;
    NeuroApp.state.isRecording = recording;
    NeuroApp.state.isMonitoring = monitoring;

    // Bouton de connexion
    const connectBtn = document.getElementById('connectBtn');
    if (connectBtn) {
      connectBtn.innerHTML = connected ?
        '<span>🔌</span>' + this.i18nSpan('btn.disconnect', 'neuro_btn-text') :
        '<span>🔗</span>' + this.i18nSpan('btn.connect', 'neuro_btn-text');
      connectBtn.className = connected ?
        'neuro_btn neuro_btn-danger' :
        'neuro_btn neuro_btn-primary';
      connectBtn.onclick = connected ? DeviceManager.disconnect : DeviceManager.connect;
    }

    // Statut de connexion
    const connectionStatus = document.getElementById('connectionStatus');
    const connectionText = document.getElementById('connectionText');
    if (connectionStatus && connectionText) {
      connectionStatus.className = connected ?
        'neuro_status-dot neuro_status-connected' :
        'neuro_status-dot neuro_status-disconnected';
      const connectionKey = connected ? 'status.connected' : 'status.disconnected';
      connectionText.setAttribute('data-i18n', connectionKey);
      connectionText.textContent = t(connectionKey);
    }

    // Bouton d'enregistrement
    const recordBtn = document.getElementById('recordBtn');
    if (recordBtn) {
      recordBtn.disabled = !connected;
      recordBtn.innerHTML = recording ?
        '<span>⏹️</span>' + this.i18nSpan('btn.recordStop', 'neuro_btn-text') :
        '<span>⏺️</span>' + this.i18nSpan('btn.record', 'neuro_btn-text');
      recordBtn.className = recording ?
        'neuro_btn neuro_btn-danger' :
        'neuro_btn neuro_btn-success';
    }

    // Statut d'enregistrement
    const recordingStatus = document.getElementById('recordingStatus');
    if (recordingStatus) {
      recordingStatus.style.display = recording ? 'flex' : 'none';
    }

    // Bouton de téléchargement
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
      downloadBtn.disabled = !connected;
    }

    this.updateSystemStatus(connected, monitoring);
  },

  updateDeviceStatus(deviceStatus) {
    NeuroApp.state.deviceStatus = deviceStatus;

    const deviceIndicator = document.getElementById('deviceStatusIndicator');
    const deviceDot = document.getElementById('deviceStatusDot');
    const deviceText = document.getElementById('deviceStatusText');

    if (deviceIndicator && deviceDot && deviceText) {
      if (deviceStatus.online) {
        deviceIndicator.style.display = 'flex';
        deviceDot.className = 'neuro_status-dot neuro_status-connected';

        let statusText = 'Crown';
        if (deviceStatus.battery !== undefined && deviceStatus.battery !== 'unknown') {
          const batteryIcon = deviceStatus.charging ? '⚡' : '🔋';
          statusText += ` ${batteryIcon} ${deviceStatus.battery}%`;
        }

        // Valeur dynamique : on retire la clé statique pour ne pas l'écraser
        deviceText.removeAttribute('data-i18n');
        deviceText.textContent = statusText;
      } else {
        deviceIndicator.style.display = 'none';
      }
    }
  },

  updateBatteryStatus(data) {
    if (!data || data.level === undefined) return;

    const level = data.level;
    const charging = data.charging;

    NeuroApp.state.deviceStatus.battery = level;
    NeuroApp.state.deviceStatus.charging = charging;

    // Icône et couleur selon le niveau
    let batteryIcon = charging ? '⚡' : (level <= 20 ? '🪫' : '🔋');
    let colorClass = level <= 20 ? 'battery-low' : (level <= 50 ? 'battery-medium' : 'battery-good');

    // Mise à jour du statut système
    const batteryEl = document.getElementById('systemBattery');
    if (batteryEl) {
      batteryEl.innerHTML = `<span class="${colorClass}">${batteryIcon} ${level}%</span>`;
      batteryEl.classList.toggle('battery-charging', charging);
    }

    // Mise à jour dans la navbar
    this.updateDeviceStatus(NeuroApp.state.deviceStatus);
  },

  updateMonitoringStatus(monitoring) {
    const charts = document.querySelectorAll('.neuro_chart-card');
    charts.forEach(chart => {
      chart.style.borderLeft = monitoring ? '4px solid #10b981' : '';
      chart.style.boxShadow = monitoring ? '0 0 20px rgba(16, 185, 129, 0.1)' : '';
    });
  },

  updateCircularProgress(type, value, timestamp) {
    const circumference = 2 * Math.PI * 65;
    const progress = Math.min(Math.max(value, 0), 100);
    const offset = circumference - (progress / 100) * circumference;

    const progressEl = document.getElementById(`${type}Progress`);
    const valueEl = document.getElementById(`${type}Value`);
    const timestampEl = document.getElementById(`${type}Timestamp`);

    if (progressEl) {
      progressEl.style.strokeDasharray = circumference;
      progressEl.style.strokeDashoffset = offset;
    }

    if (valueEl) {
      valueEl.textContent = Math.round(progress) + '%';
    }

    if (timestampEl) {
      if (timestamp) timestampEl.dataset.timestamp = timestamp;
      timestampEl.textContent = I18n.formatTime(timestampEl.dataset.timestamp) + ' ✓';
    }
  },

  updateSystemStatus(connected, monitoring) {
    const setKey = (id, key) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.setAttribute('data-i18n', key);
      el.textContent = t(key);
    };

    setKey('systemConnectionStatus', connected ? 'status.connected' : 'status.disconnected');
    setKey('systemMonitoringStatus', monitoring ? 'system.active' : 'system.stopped');
  },

 updateElectrodeQuality(electrode, qualityData) {
    const electrodeEl = document.querySelector(`[data-electrode="${electrode}"]`);
    if (!electrodeEl) {
      console.warn(`Élément DOM pour électrode ${electrode} non trouvé`);
      return;
    }

    // Extraire le status et la déviation standard
    const status = qualityData.status || 'noContact';
    const standardDeviation = qualityData.standardDeviation || 0;

    // Log pour debug
    console.debug(`Électrode ${electrode}: status=${status}, stdDev=${standardDeviation}`);

    // Mettre à jour le texte de pourcentage basé sur le status
    const valueEl = electrodeEl.querySelector('.neuro_electrode-svg-value');
    if (valueEl) {
      // Mapping status → pourcentage visuel
      const displayText = {
        'great': '100%',
        'good': '75%',
        'bad': '25%',
        'noContact': '0%'
      };
      valueEl.textContent = displayText[status] || '0%';
    }

    // Supprimer toutes les classes de qualité existantes
    electrodeEl.classList.remove('neuro_quality-good', 'neuro_quality-medium', 'neuro_quality-poor');

    // Appliquer la classe appropriée selon le status
    // great → vert (neuro_quality-good)
    // good → jaune (neuro_quality-medium)
    // bad → rouge (neuro_quality-poor)
    // noContact → rouge (neuro_quality-poor)
    const qualityClass = {
      'great': 'neuro_quality-good',
      'good': 'neuro_quality-medium',
      'bad': 'neuro_quality-poor',
      'noContact': 'neuro_quality-poor'
    };

    const classToAdd = qualityClass[status] || 'neuro_quality-poor';
    electrodeEl.classList.add(classToAdd);

    console.debug(`Électrode ${electrode} classe appliquée: ${classToAdd}`);
  },

  hideLoader() {
    const loader = document.getElementById('initialLoader');
    if (loader) {
      loader.classList.add('neuro_hidden');
      setTimeout(() => loader.remove(), 500);
    }
    document.body.classList.add('neuro_loaded');
  }
};

// ===============================================
// GESTIONNAIRE DE PÉRIPHÉRIQUE
// ===============================================

const DeviceManager = {
  async connect() {
    const connectBtn = document.getElementById('connectBtn');
    if (connectBtn) {
      connectBtn.disabled = true;
      connectBtn.innerHTML = UI.i18nSpan('btn.connecting', 'neuro_btn-text');
    }

    UI.showToast(t('toast.connecting'), 'info', 3000);

    try {
      const response = await fetch('/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await response.json();

      if (data.success) {
        UI.showToast(I18n.fromServer(data, 'toast.connected'), 'success');
        UI.updateConnectionStatus(true, false, false);
        UI.updateDeviceStatus(data.device_status || {});

        // Démarrer le monitoring automatiquement
        setTimeout(() => {
          if (SocketManager.socket && SocketManager.socket.connected) {
            SocketManager.emit('start_monitoring');
          }
        }, 1000);
      } else {
        UI.showToast(I18n.fromServer(data, 'toast.connectError'), 'error', 8000);
      }
    } catch (error) {
      console.error('Erreur connexion:', error);
      UI.showToast(t('toast.networkError'), 'error');
    } finally {
      if (connectBtn) {
        connectBtn.disabled = false;
      }
    }
  },

  async disconnect() {
    if (!confirm(t('confirm.disconnect'))) return;

    try {
      const response = await fetch('/disconnect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await response.json();

      if (data.success) {
        UI.showToast(t('toast.disconnected'), 'success');

        if (NeuroApp.state.isMonitoring) {
          SocketManager.emit('stop_monitoring');
        }

        UI.updateConnectionStatus(false, false, false);

        // Réinitialiser les électrodes
        document.querySelectorAll('.neuro_electrode-svg').forEach(el => {
          el.classList.remove('neuro_quality-good', 'neuro_quality-medium');
          el.classList.add('neuro_quality-poor');
          const valueEl = el.querySelector('.neuro_electrode-svg-value');
          if (valueEl) valueEl.textContent = '--%';
        });

        // Réinitialiser l'EEG raw
        if (NeuroApp.state.charts.eegRaw) {
          NeuroApp.state.charts.eegRaw.dataBuffer = [];
          NeuroApp.state.charts.eegRaw.draw();
        }
      }
    } catch (error) {
      console.error('Erreur déconnexion:', error);
      UI.showToast(t('toast.networkError'), 'error');
    }
  }
};

// ===============================================
// GESTIONNAIRE D'ENREGISTREMENT
// ===============================================

const RecordingManager = {
  async toggle() {
    if (!NeuroApp.state.isConnected) {
      UI.showToast(t('toast.connectFirst'), 'warning');
      return;
    }

    const endpoint = NeuroApp.state.isRecording ? '/stop_recording' : '/start_recording';

    UI.showToast(
      t(NeuroApp.state.isRecording ? 'toast.recording.stopping' : 'toast.recording.starting'),
      'info'
    );

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      const result = await response.json();

      if (result.success) {
        NeuroApp.state.isRecording = result.recording;
        UI.showToast(
          t(NeuroApp.state.isRecording ? 'toast.recording.started' : 'toast.recording.stopped'),
          'success'
        );

        if (!NeuroApp.state.isRecording) {
          setTimeout(() => SessionsManager.load(), 1000);
        }

        UI.updateConnectionStatus(
          NeuroApp.state.isConnected,
          NeuroApp.state.isRecording,
          NeuroApp.state.isMonitoring
        );
      } else {
        UI.showToast(t('toast.error', { message: I18n.fromServer(result, 'toast.unknownError') }), 'error');
      }
    } catch (error) {
      console.error('Erreur enregistrement:', error);
      UI.showToast(t('toast.networkError'), 'error');
    }
  },

  async download() {
    try {
      UI.showToast(t('toast.searchingSession'), 'info');

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

        UI.showToast(t('toast.downloading', { file: latestSession }), 'success');
      } else {
        UI.showToast(t('toast.noSession'), 'warning');
      }
    } catch (error) {
      console.error('Erreur téléchargement:', error);
      UI.showToast(t('toast.downloadError'), 'error');
    }
  }
};

// ===============================================
// GESTIONNAIRE DE SESSIONS
// ===============================================

const SessionsManager = {
  async load() {
    try {
      const response = await fetch('/sessions');
      const data = await response.json();
      this.display(data.sessions || []);
    } catch (error) {
      console.error('Erreur chargement sessions:', error);
      document.getElementById('sessionsList').innerHTML =
        `<p style="color: #ef4444;" data-i18n="sessions.loadError">${t('sessions.loadError')}</p>`;
    }
  },

  display(sessions) {
    const sessionsList = document.getElementById('sessionsList');
    if (!sessionsList) return;

    NeuroApp.state.sessions = sessions;

    // Mise à jour du compteur
    const counter = document.getElementById('sessionsCounter');
    if (counter) {
      // Valeur interpolée : retraduite via un rendu complet au changement de langue
      counter.removeAttribute('data-i18n');
      counter.textContent = I18n.plural('sessions.count', sessions.length);
    }

    // Mise à jour des statistiques
    document.getElementById('totalSessions').textContent = sessions.length;
    document.getElementById('totalSize').textContent =
      sessions.length < 1 ? '0 KB' : `${(sessions.length * 0.4).toFixed(1)} MB`;

    if (sessions.length === 0) {
      sessionsList.innerHTML = `
        <div class="neuro_sessions-empty">
          <span data-i18n="sessions.empty">${t('sessions.empty')}</span>
          <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.7;" data-i18n="sessions.emptyCreate">
            ${t('sessions.emptyCreate')}
          </div>
        </div>
      `;
      return;
    }

    // Afficher les sessions avec bouton de visualisation
    sessionsList.innerHTML = sessions.map((session, index) => {
      const dateMatch = session.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
      let displayDate = '';
      let displayTime = '';

      if (dateMatch) {
        const [, year, month, day, hour, minute] = dateMatch;
        displayDate = I18n.formatDate(year, month, day);
        displayTime = `${hour}:${minute}`;
      }

      return `
        <div class="neuro_session-item" style="animation-delay: ${(index % 10) * 0.05}s">
          <div class="neuro_session-info">
            <div class="neuro_session-name">${session}</div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.25rem;">
              <span>📅 ${displayDate}</span>
              <span style="margin-left: 1rem;">🕐 ${displayTime}</span>
            </div>
          </div>
          <div class="neuro_session-actions">
            <button class="neuro_btn neuro_btn-primary neuro_btn-small"
                    onclick="SessionsManager.visualize('${session}')"
                    data-i18n-attr="title:sessions.visualize.title"
                    title="${t('sessions.visualize.title')}">
              <span>📊</span> <span data-i18n="sessions.visualize">${t('sessions.visualize')}</span>
            </button>
            <button class="neuro_btn neuro_btn-outline neuro_btn-small"
                    onclick="SessionsManager.download('${session}')"
                    data-i18n-attr="title:sessions.csv.title"
                    title="${t('sessions.csv.title')}">
              <span>⬇️</span> CSV
            </button>
          </div>
        </div>
      `;
    }).join('');
  },

  download(filename) {
    const link = document.createElement('a');
    link.href = `/download/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    UI.showToast(t('toast.downloading', { file: filename }), 'success');
  },

  visualize(filename) {
    // Ouvrir la page de visualisation dans un nouvel onglet
    const url = `/viewer?file=${encodeURIComponent(filename)}`;
    window.open(url, '_blank');
    UI.showToast(t('toast.opening'), 'info');
  },

  refresh() {
    const btn = document.querySelector('.neuro_sessions-refresh-btn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = UI.i18nSpan('sessions.refreshing', 'neuro_btn-text');
    }

    UI.showToast(t('toast.refreshingSessions'), 'info', 2000);

    this.load().finally(() => {
      if (btn) {
        setTimeout(() => {
          btn.disabled = false;
          btn.innerHTML = '<span>🔄</span>' + UI.i18nSpan('sessions.refresh', 'neuro_btn-text');
        }, 1000);
      }
    });
  }
};

// ===============================================
// GESTIONNAIRE DE GRAPHIQUES
// ===============================================

const ChartManager = {
  init() {
    const canvas = document.getElementById('brainwavesChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    NeuroApp.state.charts.brainwaves = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: [
          'Delta\n0.1-4 Hz',
          'Theta\n4-7.5 Hz',
          'Alpha\n7.5-12.5 Hz',
          'Beta\n12.5-30 Hz',
          'Gamma\n30-100 Hz'
        ],
        datasets: [{
          label: t('chart.power.label'),
          data: [0, 0, 0, 0, 0],
          backgroundColor: [
            'rgba(99, 102, 241, 0.8)',
            'rgba(245, 158, 11, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(34, 197, 94, 0.8)',
            'rgba(236, 72, 153, 0.8)'
          ],
          borderColor: [
            'rgb(99, 102, 241)',
            'rgb(245, 158, 11)',
            'rgb(59, 130, 246)',
            'rgb(34, 197, 94)',
            'rgb(236, 72, 153)'
          ],
          borderWidth: 1,
          barThickness: 'flex',
          maxBarThickness: 100,
          categoryPercentage: 0.8,
          barPercentage: 0.9
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: NeuroApp.config.chartUpdateAnimation,
          easing: 'linear'
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            callbacks: {
              title: (context) => context[0].label.split('\n')[0],
              label: (context) => context.parsed.y.toFixed(1) + ' μV²/Hz'
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              font: { family: 'Inter, sans-serif', size: 11 },
              color: '#64748b'
            }
          },
          y: {
            min: 0,
            max: 30,
            grid: { color: 'rgba(0, 0, 0, 0.05)' },
            ticks: {
              stepSize: 2,
              font: { family: 'Inter, sans-serif', size: 11 },
              color: '#94a3b8',
              callback: (value) => value % 2 === 0 ? value + ' μV²/Hz' : ''
            }
          }
        }
      }
    });
  },

  initEEGRaw() {
    const canvas = document.getElementById('eegRawChart');
    if (!canvas) return;

    NeuroApp.state.charts.eegRaw = new EEGRawChart(canvas);
  },

  /**
   * Réapplique la langue courante aux graphiques (légendes, infobulles, axes).
   */
  applyLanguage() {
    const chart = NeuroApp.state.charts.brainwaves;
    if (!chart) return;

    chart.data.datasets[0].label = t('chart.power.label');
    chart.update('none');
  }
};

// ===============================================
// UTILITAIRES
// ===============================================

const Utils = {
  formatTimestamp(timestamp) {
    return I18n.formatTime(timestamp);
  },

  initClock() {
    const timeEl = document.getElementById('currentTime');
    if (!timeEl) return;

    const updateClock = () => {
      timeEl.textContent = I18n.formatTime(Date.now());
    };

    updateClock();
    setInterval(updateClock, 1000);
  }
};

// ===============================================
// INITIALISATION
// ===============================================

function initializeApp() {
  console.log('Démarrage Neurosity Monitor...');

  // Cacher le loader
  setTimeout(() => UI.hideLoader(), 1000);

  // Initialiser l'horloge
  Utils.initClock();

  // Initialiser WebSocket
  SocketManager.init();

  // Initialiser les graphiques
  ChartManager.init();
  ChartManager.initEEGRaw();

  // Charger les sessions
  SessionsManager.load();

  // Initialiser les électrodes
  document.querySelectorAll('.neuro_electrode-svg').forEach(el => {
    el.classList.add('neuro_quality-poor');
  });

  // Réappliquer la langue à tout ce qui est généré dynamiquement
  I18n.onChange(applyLanguage);

  // Message de bienvenue
  UI.showToast(t('toast.welcome'), 'info', 8000);
}

/**
 * Rejoue le rendu de tout ce que le JS a produit dynamiquement :
 * statuts, boutons, horodatages, liste des sessions et graphiques.
 */
function applyLanguage() {
  UI.updateConnectionStatus(
    NeuroApp.state.isConnected,
    NeuroApp.state.isRecording,
    NeuroApp.state.isMonitoring
  );
  UI.updateDeviceStatus(NeuroApp.state.deviceStatus || {});
  UI.updateLastUpdate('brainwavesTimestamp');
  UI.updateLastUpdate('eegRawTimestamp');

  ['calm', 'focus'].forEach(type => {
    const el = document.getElementById(`${type}Timestamp`);
    if (el && el.dataset.timestamp) {
      el.textContent = I18n.formatTime(el.dataset.timestamp) + ' ✓';
    }
  });

  SessionsManager.display(NeuroApp.state.sessions || []);
  ChartManager.applyLanguage();
  UI.showToast(t('toast.langChanged'), 'info', 2000);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', initializeApp);

window.addEventListener('beforeunload', (event) => {
  if (NeuroApp.state.isRecording) {
    event.preventDefault();
    event.returnValue = t('confirm.unload');
    return event.returnValue;
  }
});

// Raccourcis clavier
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey || e.metaKey) {
    switch(e.key) {
      case 'k':
        e.preventDefault();
        if (NeuroApp.state.isConnected) {
          DeviceManager.disconnect();
        } else {
          DeviceManager.connect();
        }
        break;
      case 'r':
        e.preventDefault();
        if (NeuroApp.state.isConnected) {
          RecordingManager.toggle();
        }
        break;
    }
  }
});

// Exports globaux
window.connectDevice = () => DeviceManager.connect();
window.disconnectDevice = () => DeviceManager.disconnect();
window.toggleRecording = () => RecordingManager.toggle();
window.downloadData = () => RecordingManager.download();
window.SessionsManager = SessionsManager;
window.refreshSessions = () => SessionsManager.refresh();