/**
 * APPLICATION NEUROSITY MONITOR - FICHIER COMPLET UNIFIÉ
 * Interface utilisateur adaptée à la détection biologique réelle
 * Avec Sessions Manager optimisé pour milliers de fichiers
 * Classes CSS préfixées avec "neuro_"
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
    detectionInProgress: false,
    debugMode: false
};

// Variables globales centralisées (migré depuis le HTML)
window.AppUtils = {
    isInitialized: false,
    viewport: { width: 0, height: 0, isMobile: false, isTablet: false }
};

// Variables globales pour le statut de la navbar (gardées pour compatibilité)
window.NavbarState = {
    connected: false,
    recording: false,
    monitoring: false,
    deviceOnline: false
};

// ===============================================
// NOUVEAU: SESSIONS MANAGER OPTIMISÉ (adapté aux nouvelles classes)
// ===============================================

window.SessionsManager = {
    allSessions: [],
    visibleSessions: [],
    currentPage: 0,
    itemsPerPage: 50, // Afficher 50 sessions à la fois
    isVirtualizationEnabled: false,
    scrollContainer: null,

    init() {
        this.scrollContainer = document.querySelector('.neuro_sessions-scroll-container');
        if (this.scrollContainer) {
            this.setupScrollHandlers();
        }
    },

    setupScrollHandlers() {
        if (!this.scrollContainer) return;

        // Détection du scroll pour lazy loading
        this.scrollContainer.addEventListener('scroll', this.throttle(() => {
            this.handleScroll();
            this.updateScrollIndicators();
        }, 100));

        // Observer pour détecter les changements de contenu
        const observer = new MutationObserver(() => {
            this.updateScrollIndicators();
        });

        observer.observe(this.scrollContainer, {
            childList: true,
            subtree: true
        });
    },

    updateScrollIndicators() {
        if (!this.scrollContainer) return;

        const { scrollTop, scrollHeight, clientHeight } = this.scrollContainer;
        const hasScroll = scrollHeight > clientHeight;

        if (hasScroll) {
            this.scrollContainer.classList.add('neuro_has-scroll');
        } else {
            this.scrollContainer.classList.remove('neuro_has-scroll');
        }

        // Ajouter classe pour optimiser les performances avec beaucoup d'éléments
        if (this.allSessions.length > 100) {
            this.scrollContainer.classList.add('neuro_many-sessions');
        } else {
            this.scrollContainer.classList.remove('neuro_many-sessions');
        }
    },

    handleScroll() {
        if (!this.isVirtualizationEnabled || !this.scrollContainer) return;

        const { scrollTop, scrollHeight, clientHeight } = this.scrollContainer;
        const scrollPercentage = scrollTop / (scrollHeight - clientHeight);

        // Charger plus d'éléments quand on approche de la fin
        if (scrollPercentage > 0.8 && this.hasMoreSessions()) {
            this.loadMoreSessions();
        }
    },

    hasMoreSessions() {
        return (this.currentPage + 1) * this.itemsPerPage < this.allSessions.length;
    },

    loadMoreSessions() {
        if (!this.hasMoreSessions()) return;

        this.currentPage++;
        const startIndex = this.currentPage * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.allSessions.length);

        const newSessions = this.allSessions.slice(startIndex, endIndex);
        this.visibleSessions.push(...newSessions);

        this.appendSessionsToDOM(newSessions);

        // Notification discrète
        if (window.showToast) {
            window.showToast(
                `📄 ${newSessions.length} sessions supplémentaires chargées`,
                'info',
                2000
            );
        }
    },

    appendSessionsToDOM(sessions) {
        const sessionsList = document.getElementById('sessionsList');
        if (!sessionsList) return;

        const fragment = document.createDocumentFragment();

        sessions.forEach((session, index) => {
            const sessionElement = this.createSessionElement(session, this.visibleSessions.length - sessions.length + index);
            fragment.appendChild(sessionElement);
        });

        sessionsList.appendChild(fragment);
    },

    createSessionElement(session, index) {
        const sessionItem = document.createElement('div');
        sessionItem.className = 'neuro_session-item';
        sessionItem.style.animationDelay = `${(index % 10) * 0.05}s`; // Animation échelonnée par groupes de 10

        const dateMatch = session.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
        let displayDate = 'Session';
        let displayTime = '';

        if (dateMatch) {
            const [, year, month, day, hour, minute, second] = dateMatch;
            displayDate = `${day}/${month}/${year}`;
            displayTime = `${hour}:${minute}`;
        }

        sessionItem.innerHTML = `
            <div class="neuro_session-info">
                <div class="neuro_session-name">
                    ${session} 
                    <span style="color: #8b5cf6; font-size: 0.875rem;">✓</span>
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.25rem; display: flex; gap: 1rem; flex-wrap: wrap;">
                    <span>📅 ${displayDate}</span>
                    <span>🕒 ${displayTime}</span>
                    <span style="color: #8b5cf6;">🔬 Données biologiques validées</span>
                </div>
            </div>
            <div class="neuro_session-actions">
                <button class="neuro_btn neuro_btn-outline neuro_btn-small" onclick="downloadSession('${session}')" title="Télécharger CSV validé">
                    <span>⬇️</span> CSV
                </button>
            </div>
        `;

        return sessionItem;
    },

    // Fonction throttle pour optimiser les performances
    throttle(func, limit) {
        let lastFunc;
        let lastRan;
        return function() {
            const context = this;
            const args = arguments;
            if (!lastRan) {
                func.apply(context, args);
                lastRan = Date.now();
            } else {
                clearTimeout(lastFunc);
                lastFunc = setTimeout(function() {
                    if ((Date.now() - lastRan) >= limit) {
                        func.apply(context, args);
                        lastRan = Date.now();
                    }
                }, limit - (Date.now() - lastRan));
            }
        }
    }
};

/**
 * Initialisation centralisée (migré depuis le HTML)
 */
function initializeBaseComponents() {
    if (window.AppUtils.isInitialized) return;

    console.log('🎨 Initialisation des composants de base...');

    // Cacher le loader après un délai
    setTimeout(hideInitialLoader, 1000);

    // Initialiser l'horloge
    initializeClock();

    // Gestion responsive
    initializeResponsive();

    // Améliorer l'accessibilité
    initializeAccessibility();

    // Gestion des erreurs globales
    initializeErrorHandling();

    // Performance monitoring
    initializePerformanceMonitoring();

    // Détection de la connexion réseau
    initializeNetworkDetection();

    window.AppUtils.isInitialized = true;
    console.log('✅ Composants de base initialisés');
}

/**
 * Gestion du loader améliorée (migré depuis le HTML)
 */
function hideInitialLoader() {
    const loader = document.getElementById('initialLoader');
    const body = document.body;

    if (loader) {
        loader.classList.add('neuro_hidden');
        setTimeout(() => {
            if (loader.parentNode) {
                loader.parentNode.removeChild(loader);
            }
        }, 500);
    }

    body.classList.add('neuro_loaded');
}

/**
 * Horloge optimisée (migré depuis le HTML)
 */
function initializeClock() {
    const timeElement = document.getElementById('currentTime');
    if (!timeElement) return;

    function updateClock() {
        try {
            const now = new Date();
            timeElement.textContent = now.toLocaleTimeString('fr-FR');
        } catch (e) {
            console.warn('Erreur mise à jour horloge:', e);
        }
    }

    updateClock();
    setInterval(updateClock, 1000);
}

/**
 * Gestion responsive centralisée (migré depuis le HTML)
 */
function initializeResponsive() {
    function updateViewport() {
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight,
            isMobile: window.innerWidth < 768,
            isTablet: window.innerWidth >= 768 && window.innerWidth < 1024
        };

        window.AppUtils.viewport = viewport;

        // CSS custom properties
        document.documentElement.style.setProperty('--vh', `${viewport.height * 0.01}px`);

        // Émettre un événement pour les autres composants
        window.dispatchEvent(new CustomEvent('viewportChange', { detail: viewport }));
    }

    window.addEventListener('resize', updateViewport);
    window.addEventListener('orientationchange', updateViewport);
    updateViewport(); // Appel initial
}

/**
 * Accessibilité améliorée (migré depuis le HTML)
 */
function initializeAccessibility() {
    // Navigation au clavier
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            document.body.classList.add('neuro_keyboard-navigation');
        }
    });

    document.addEventListener('mousedown', function() {
        document.body.classList.remove('neuro_keyboard-navigation');
    });

    // Raccourcis clavier globaux
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'k':
                    e.preventDefault();
                    if (window.connectDevice) connectDevice();
                    break;
                case 'r':
                    e.preventDefault();
                    if (window.toggleRecording) toggleRecording();
                    break;
            }
        }
    });
}

/**
 * Gestion d'erreurs centralisée (migré depuis le HTML)
 */
function initializeErrorHandling() {
    window.addEventListener('error', function(e) {
        console.error('Erreur globale:', e.error);
        if (window.showToast) {
            showToast('❌ Une erreur est survenue', 'error');
        }
    });

    // Promesses non gérées
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Promise rejetée:', e.reason);
        if (window.showToast) {
            showToast('❌ Erreur asynchrone', 'error');
        }
    });
}

/**
 * Monitoring de performance optimisé (migré depuis le HTML)
 */
function initializePerformanceMonitoring() {
    if (!('performance' in window)) return;

    window.addEventListener('load', function() {
        setTimeout(() => {
            try {
                const perfData = performance.getEntriesByType('navigation')[0];
                if (perfData) {
                    const metrics = {
                        loadTime: Math.round(perfData.loadEventEnd - perfData.fetchStart),
                        domReady: Math.round(perfData.domContentLoadedEventEnd - perfData.fetchStart)
                    };
                    console.log('⚡ Performance:', metrics);

                    // Alerter si les performances sont dégradées
                    if (metrics.loadTime > 5000) {
                        console.warn('⚠️ Temps de chargement élevé:', metrics.loadTime + 'ms');
                    }
                }
            } catch (e) {
                console.warn('Erreur monitoring performance:', e);
            }
        }, 100);
    });
}

/**
 * Détection réseau améliorée (migré depuis le HTML)
 */
function initializeNetworkDetection() {
    function updateNetworkStatus() {
        const isOnline = navigator.onLine;
        document.body.classList.toggle('neuro_offline', !isOnline);

        if (window.showToast) {
            if (isOnline) {
                showToast('🌐 Connexion rétablie', 'success', 2000);
            } else {
                showToast('📱 Mode hors ligne', 'warning', 5000);
            }
        }
    }

    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);
}

/**
 * Intersection Observer pour les animations d'entrée (migré depuis le HTML)
 */
function initializeIntersectionObserver() {
    if (!('IntersectionObserver' in window)) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('neuro_in-view');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '50px'
    });

    // Observer les éléments après un délai pour éviter la surcharge
    setTimeout(() => {
        document.querySelectorAll('.neuro_card, .neuro_metric-card, .neuro_chart-card').forEach(element => {
            observer.observe(element);
        });
    }, 500);
}

/**
 * Fonction simplifiée pour la gestion responsive (migré depuis le HTML)
 */
function handleNavbarResize() {
    const navControls = document.querySelector('.neuro_nav-controls');
    const isMobile = window.innerWidth < 768;
    const isSmallMobile = window.innerWidth < 480;

    if (navControls) {
        if (isSmallMobile) {
            // Cacher le texte des boutons sur très petits écrans
            document.querySelectorAll('.neuro_btn-text').forEach(text => {
                text.style.display = 'none';
            });
        } else {
            // Afficher le texte des boutons
            document.querySelectorAll('.neuro_btn-text').forEach(text => {
                text.style.display = 'inline';
            });
        }
    }
}

/**
 * Fonction d'actualisation spécifique à cette page (migré depuis le HTML)
 */
function refreshSessions() {
    const refreshBtn = document.querySelector('.neuro_sessions-refresh-btn');
    if (!refreshBtn) return;

    const originalText = refreshBtn.innerHTML;
    const iconSpan = refreshBtn.querySelector('span:first-child');

    // Animation du bouton
    if (iconSpan) {
        iconSpan.style.animation = 'neuro_spin 1s linear infinite';
    }
    refreshBtn.innerHTML = '<span style="animation: neuro_spin 1s linear infinite;">🔄</span> <span class="neuro_btn-text">Actualisation...</span>';
    refreshBtn.disabled = true;

    if (window.showToast) {
        showToast('🔄 Actualisation des sessions...', 'info', 2000);
    }

    // Appeler la fonction globale loadSessions
    if (window.loadSessions) {
        window.loadSessions().finally(() => {
            setTimeout(() => {
                refreshBtn.innerHTML = originalText;
                refreshBtn.disabled = false;
                if (iconSpan) {
                    iconSpan.style.animation = '';
                }
            }, 1000);
        });
    } else {
        // Fallback si loadSessions n'est pas disponible
        setTimeout(() => {
            refreshBtn.innerHTML = originalText;
            refreshBtn.disabled = false;
        }, 1000);
    }
}

/**
 * Initialisation au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Démarrage Neurosity Monitor');

    // Initialisation centralisée
    initializeBaseComponents();

    initializeUI();
    initializeCharts();
    initializeWebSocket();
    loadSessions();

    // Initialiser le gestionnaire de sessions optimisé
    window.SessionsManager.init();

    // Gestion responsive initiale (migré depuis le HTML)
    handleNavbarResize();

    // Animation de chargement des éléments de la navbar (migré depuis le HTML)
    const navElements = document.querySelectorAll('.neuro_nav-controls > *');
    navElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(-10px)';

        setTimeout(() => {
            element.style.transition = 'all 0.3s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 100 * (index + 1));
    });

    // Animation d'entrée pour les éléments de cette page (migré depuis le HTML)
    const cards = document.querySelectorAll('.neuro_dashboard-grid .neuro_card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';

        setTimeout(() => {
            card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 200 * (index + 1));
    });

    // Initialiser l'intersection observer
    setTimeout(initializeIntersectionObserver, 1000);

    showToast('🧠 Application prête ! Détection activée - Allumez votre casque Neurosity Crown puis cliquez "Connecter"', 'info', 8000);
    console.log('✅ Application prête avec détection et Sessions Manager optimisé');
});

// Écouteurs d'événements pour la navbar (uniquement responsive) (migré depuis le HTML)
window.addEventListener('resize', handleNavbarResize);
window.addEventListener('orientationchange', handleNavbarResize);

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
    toast.className = `neuro_toast neuro_toast-${type}`;
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
    const navbar = document.querySelector('.neuro_navbar');
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
            updateConnectionStatus(window.AppState.isConnected, window.AppState.isRecording, true);
        });

        window.AppState.socket.on('monitoring_stopped', function() {
            showToast('⏹️ Monitoring arrêté', 'info');
            window.AppState.isMonitoring = false;
            updateMonitoringStatus(false);
            updateConnectionStatus(window.AppState.isConnected, window.AppState.isRecording, false);
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
 * Gestion dynamique du bouton de connexion
 */
function updateConnectionButton(connected) {
    const connectBtn = document.getElementById('connectBtn');
    if (!connectBtn) return;

    if (connected) {
        connectBtn.innerHTML = '<span>🔌</span><span class="neuro_btn-text">Déconnecter</span>';
        connectBtn.className = 'neuro_btn neuro_btn-danger';
        connectBtn.onclick = disconnectDevice;
        connectBtn.title = 'Déconnecter le casque Neurosity';
    } else {
        connectBtn.innerHTML = '<span>🔗</span><span class="neuro_btn-text">Connecter</span>';
        connectBtn.className = 'neuro_btn neuro_btn-primary';
        connectBtn.onclick = connectDevice;
        connectBtn.title = 'Connecter le casque Neurosity (Ctrl+K)';
    }
}

/**
 * Fonction de déconnexion mise à jour
 */
function disconnectDevice() {
    if (!confirm('Êtes-vous sûr de vouloir déconnecter le casque ?')) {
        return;
    }

    const connectBtn = document.getElementById('connectBtn');
    if (connectBtn) {
        connectBtn.disabled = true;
        connectBtn.innerHTML = '<span>⏳</span><span class="neuro_btn-text">Déconnexion...</span>';
    }

    fetch('/disconnect', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('🔌 Casque déconnecté', 'success');
            updateConnectionButton(false);

            // Arrêter le monitoring s'il était actif
            if (window.AppState.isMonitoring) {
                stopMonitoring();
            }

            // Mettre à jour tous les statuts
            window.AppState.isConnected = false;
            window.AppState.isMonitoring = false;
            updateConnectionStatus(false, false, false);
        } else {
            showToast('❌ Erreur déconnexion: ' + (data.error || 'Erreur inconnue'), 'error');
        }
    })
    .catch(error => {
        console.error('Erreur déconnexion:', error);
        showToast('❌ Erreur de déconnexion', 'error');
    })
    .finally(() => {
        if (connectBtn) {
            connectBtn.disabled = false;
        }
    });
}

/**
 * Connecte le casque avec interface de détection stricte
 */
function connectDevice() {
    const connectBtn = document.getElementById('connectBtn');
    if (connectBtn) {
        connectBtn.disabled = true;
        connectBtn.innerHTML = '<span>⏳</span><span class="neuro_btn-text">Connexion...</span>';
    }

    showToast('🔄 Connexion en cours...', 'info', 3000);

    fetch('/connect', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('✅ ' + (data.message || 'Casque connecté avec succès !'), 'success');
            updateConnectionButton(true);

            // Mettre à jour l'état global
            window.AppState.isConnected = true;
            window.AppState.deviceStatus = data.device_status || {};

            updateConnectionStatus(true, false, false);
            updateDeviceStatus(data.device_status || {});

            // Démarrer automatiquement le monitoring
            setTimeout(() => {
                console.log('🎯 Démarrage automatique du monitoring...');
                startMonitoring();
            }, 1000);

        } else {
            showToast('❌ ' + (data.error || 'Erreur de connexion'), 'error', 8000);
            updateConnectionButton(false);
            window.AppState.isConnected = false;
            updateConnectionStatus(false, false, false);
        }
    })
    .catch(error => {
        console.error('Erreur connexion:', error);
        showToast('❌ Erreur de connexion réseau', 'error');
        updateConnectionButton(false);
        window.AppState.isConnected = false;
        updateConnectionStatus(false, false, false);
    })
    .finally(() => {
        if (connectBtn) {
            connectBtn.disabled = false;
        }
    });
}

/**
 * Démarre le monitoring
 */
function startMonitoring() {
    if (!window.AppState.socket) {
        console.error('❌ Socket non disponible pour le monitoring');
        showToast('❌ Erreur WebSocket - impossible de démarrer le monitoring', 'error');
        return;
    }

    if (!window.AppState.isConnected) {
        console.warn('⚠️ Tentative de démarrage monitoring sans connexion');
        showToast('⚠️ Connectez d\'abord votre casque Neurosity Crown', 'warning');
        return;
    }

    if (window.AppState.isMonitoring) {
        console.log('🎯 Monitoring déjà actif');
        return;
    }

    console.log('🎯 Envoi commande start_monitoring...');
    showToast('🎯 Démarrage du monitoring...', 'info', 2000);

    try {
        window.AppState.socket.emit('start_monitoring');
    } catch (error) {
        console.error('❌ Erreur émission start_monitoring:', error);
        showToast('❌ Erreur de démarrage du monitoring', 'error');
    }
}

/**
 * Arrête le monitoring
 */
function stopMonitoring() {
    if (!window.AppState.socket) {
        console.error('❌ Socket non disponible pour arrêter le monitoring');
        return;
    }

    if (!window.AppState.isMonitoring) {
        console.log('⏹️ Monitoring déjà arrêté');
        return;
    }

    console.log('⏹️ Envoi commande stop_monitoring...');
    showToast('⏹️ Arrêt du monitoring...', 'info', 2000);

    try {
        window.AppState.socket.emit('stop_monitoring');
    } catch (error) {
        console.error('❌ Erreur émission stop_monitoring:', error);
        showToast('❌ Erreur d\'arrêt du monitoring', 'error');
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
            deviceDot.className = 'neuro_status-dot neuro_status-connected';

            // Information enrichie avec validation
            let statusText = 'Crown';

            if (deviceStatus.validation === 'biological_data_confirmed_v2') {
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

    // Mettre à jour le statut système
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
            connectionStatus.className = 'neuro_status-dot neuro_status-connected';
        } else {
            connectionStatus.className = 'neuro_status-dot neuro_status-recording'; // Orange pour warning
        }
    }
}

/**
 * Met à jour le statut de monitoring
 */
function updateMonitoringStatus(monitoring) {
    const charts = document.querySelectorAll('.neuro_chart-card');
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
 * Initialise les graphiques en barres pour les ondes cérébrales
 * Utilise la Densité Spectrale de Puissance (PSD) pour voir les micro-variations
 */
function initializeCharts() {
    console.log('📊 Initialisation des graphiques PSD en barres...');

    const canvas = document.getElementById('brainwavesChart');
    if (!canvas) {
        console.error('❌ Canvas non trouvé');
        return;
    }

    if (window.AppState.chart) {
        window.AppState.chart.destroy();
    }

    const ctx = canvas.getContext('2d');

    // Configuration pour graphique en barres
    window.AppState.chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [
                'Delta\n0.5-4 Hz',
                'Theta\n4-8 Hz',
                'Alpha\n8-12 Hz',
                'Beta\n12-30 Hz',
                'Gamma\n30+ Hz'
            ],
            datasets: [{
                label: 'Densité Spectrale de Puissance (μV²/Hz)',
                data: [0, 0, 0, 0, 0],
                backgroundColor: [
                    'rgba(99, 102, 241, 0.8)',   // Delta - Bleu indigo
                    'rgba(139, 92, 246, 0.8)',   // Theta - Violet
                    'rgba(16, 185, 129, 0.8)',   // Alpha - Vert
                    'rgba(245, 158, 11, 0.8)',   // Beta - Orange
                    'rgba(239, 68, 68, 0.8)'     // Gamma - Rouge
                ],
                borderColor: [
                    '#6366f1',  // Delta
                    '#8b5cf6',  // Theta
                    '#10b981',  // Alpha
                    '#f59e0b',  // Beta
                    '#ef4444'   // Gamma
                ],
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 150,
                easing: 'easeOutQuint'
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Ondes Cérébrales Validées - Temps Réel',
                    font: {
                        family: 'Inter',
                        size: 16,
                        weight: '600'
                    },
                    color: '#334155',
                    padding: 20
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true,
                    callbacks: {
                        title: function(context) {
                            return context[0].label.split('\n')[0];
                        },
                        label: function(context) {
                            return `${context.parsed.y.toFixed(4)} μV²/Hz`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Types d\'ondes cérébrales',
                        font: {
                            family: 'Inter',
                            size: 14,
                            weight: '500'
                        },
                        color: '#64748b',
                        padding: 10
                    },
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: 'Inter',
                            size: 11,
                            weight: '500'
                        },
                        color: '#64748b',
                        maxRotation: 0,
                        padding: 10
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Densité Spectrale de Puissance (μV²/Hz)',
                        font: {
                            family: 'Inter',
                            size: 14,
                            weight: '500'
                        },
                        color: '#64748b',
                        padding: 10
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.08)',
                        drawBorder: false,
                        lineWidth: 1
                    },
                    ticks: {
                        font: {
                            family: 'Inter',
                            size: 11
                        },
                        color: '#94a3b8',
                        padding: 8,
                        callback: function(value) {
                            return value.toFixed(3) + ' μV²/Hz';
                        }
                    },
                    beginAtZero: true,
                    max: 0.5
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            elements: {
                bar: {
                    borderRadius: 8,
                    borderWidth: 2
                }
            }
        }
    });

    console.log('✅ Graphique en barres créé avec PSD (Power Spectral Density)');
}

/**
 * Gère l'enregistrement
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
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
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
        } else {
            showToast('❌ Erreur enregistrement: ' + (result.error || 'Erreur inconnue'), 'error');
        }

        updateConnectionStatus(window.AppState.isConnected, window.AppState.isRecording, window.AppState.isMonitoring);

    } catch (error) {
        console.error('❌ Erreur enregistrement:', error);
        showToast('❌ Erreur d\'enregistrement: ' + error.message, 'error');
    }
}

/**
 * Télécharge les données
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

    const recordBtn = document.getElementById('recordBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const connectionStatus = document.getElementById('connectionStatus');
    const connectionText = document.getElementById('connectionText');
    const recordingStatus = document.getElementById('recordingStatus');

    // Mettre à jour le bouton de connexion séparément
    updateConnectionButton(connected);

    // Statut de connexion
    if (connectionStatus && connectionText) {
        if (connected) {
            connectionStatus.className = 'neuro_status-dot neuro_status-connected';
            connectionText.textContent = 'Connecté (Validé)';
        } else {
            connectionStatus.className = 'neuro_status-dot neuro_status-disconnected';
            connectionText.textContent = 'Déconnecté';
        }
    }

    // Bouton d'enregistrement
    if (recordBtn) {
        recordBtn.disabled = !connected;

        if (recording) {
            recordBtn.innerHTML = '<span>⏹️</span><span class="neuro_btn-text"> Arrêter</span>';
            recordBtn.className = 'neuro_btn neuro_btn-danger';
        } else {
            recordBtn.innerHTML = '<span>⏺️</span><span class="neuro_btn-text"> Enregistrer</span>';
            recordBtn.className = 'neuro_btn neuro_btn-success';
        }
    }

    // Bouton de téléchargement
    if (downloadBtn) {
        downloadBtn.disabled = !connected;
    }

    // Statut d'enregistrement
    if (recordingStatus) {
        if (recording) {
            recordingStatus.style.display = 'flex';
        } else {
            recordingStatus.style.display = 'none';
        }
    }

    console.log(`🔄 Statut mis à jour: Connected=${connected}, Recording=${recording}, Monitoring=${monitoring}`);
}

/**
 * Gestionnaires des données en temps réel
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

/**
 * Gestionnaire des données brainwaves pour graphique en barres
 */
function handleBrainwavesData(data) {
    if (!window.AppState.isConnected || !window.AppState.chart) return;

    window.AppState.lastDataTime = new Date();

    const chart = window.AppState.chart;

    // Calculer les moyennes pour chaque type d'onde
    const avgData = {
        delta: calculateAverage(data.delta),
        theta: calculateAverage(data.theta),
        alpha: calculateAverage(data.alpha),
        beta: calculateAverage(data.beta),
        gamma: calculateAverage(data.gamma)
    };

    // Mettre à jour les données du graphique en barres
    chart.data.datasets[0].data = [
        avgData.delta,
        avgData.theta,
        avgData.alpha,
        avgData.beta,
        avgData.gamma
    ];

    // Mise à jour du graphique avec animation vive
    chart.update('none');

    // Mettre à jour le timestamp
    const timestampElement = document.getElementById('brainwavesTimestamp');
    if (timestampElement) {
        timestampElement.textContent = 'Dernière validation: ' + formatTimestamp(data.timestamp);
    }

    // Animation visuelle pour indiquer la réception de nouvelles données
    flashDataIndicator('brainwaves');

    // Log des données pour debug
    if (window.AppState.debugMode) {
        console.log('📊 Ondes cérébrales (μV²/Hz):', {
            delta: avgData.delta.toFixed(4),
            theta: avgData.theta.toFixed(4),
            alpha: avgData.alpha.toFixed(4),
            beta: avgData.beta.toFixed(4),
            gamma: avgData.gamma.toFixed(4)
        });
    }
}

/**
 * Indicateur visuel de réception de données
 */
function flashDataIndicator(type) {
    const elements = {
        'calm': document.querySelector('.neuro_metric-card:nth-child(1)'),
        'focus': document.querySelector('.neuro_metric-card:nth-child(2)'),
        'brainwaves': document.querySelector('.neuro_chart-card')
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
 * NOUVELLE FONCTION: Fonction displaySessions optimisée pour les grandes listes
 */
function displaySessionsOptimized(sessions) {
    const sessionsList = document.getElementById('sessionsList');
    if (!sessionsList) return;

    // Sauvegarder toutes les sessions
    window.SessionsManager.allSessions = [...sessions];
    window.SessionsManager.currentPage = 0;
    window.SessionsManager.visibleSessions = [];

    // Décider si utiliser la virtualisation
    const useVirtualization = sessions.length > 100;
    window.SessionsManager.isVirtualizationEnabled = useVirtualization;

    if (sessions.length === 0) {
        sessionsList.innerHTML = `
            <div class="neuro_sessions-empty">
                Aucune session validée enregistrée
                <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.7;">
                    Connectez votre casque avec détection pour créer une session
                </div>
            </div>
        `;
        sessionsList.className = 'neuro_sessions-empty';

        // Mettre à jour les statistiques
        updateSessionsStats([]);
        return;
    }

    // Vider la liste
    sessionsList.className = '';
    sessionsList.innerHTML = '';

    if (useVirtualization) {
        // Chargement initial avec virtualisation
        console.log(`📊 Virtualisation activée pour ${sessions.length} sessions`);

        const initialSessions = sessions.slice(0, window.SessionsManager.itemsPerPage);
        window.SessionsManager.visibleSessions = [...initialSessions];

        // Créer les éléments DOM
        const fragment = document.createDocumentFragment();
        initialSessions.forEach((session, index) => {
            const sessionElement = window.SessionsManager.createSessionElement(session, index);
            fragment.appendChild(sessionElement);
        });
        sessionsList.appendChild(fragment);

        // Ajouter un indicateur de chargement progressif
        if (window.SessionsManager.hasMoreSessions()) {
            const loadMoreIndicator = document.createElement('div');
            loadMoreIndicator.className = 'neuro_load-more-indicator';
            loadMoreIndicator.innerHTML = `
                <div style="text-align: center; padding: 1rem; color: #8b5cf6; font-size: 0.875rem;">
                    📄 ${sessions.length - window.SessionsManager.itemsPerPage} sessions supplémentaires disponibles
                    <br>
                    <small style="opacity: 0.7;">Faites défiler pour charger automatiquement</small>
                </div>
            `;
            sessionsList.appendChild(loadMoreIndicator);
        }

        if (window.showToast) {
            window.showToast(
                `📊 ${initialSessions.length}/${sessions.length} sessions affichées (chargement progressif activé)`,
                'info',
                4000
            );
        }
    } else {
        // Affichage normal pour les petites listes
        console.log(`📊 Affichage normal pour ${sessions.length} sessions`);

        const fragment = document.createDocumentFragment();
        sessions.forEach((session, index) => {
            const sessionElement = window.SessionsManager.createSessionElement(session, index);
            fragment.appendChild(sessionElement);
        });
        sessionsList.appendChild(fragment);

        if (sessions.length > 0) {
            if (window.showToast) {
                window.showToast(
                    `📁 ${sessions.length} session(s) validée(s) trouvée(s)`,
                    'info',
                    2000
                );
            }
        }
    }

    // Mettre à jour les statistiques
    updateSessionsStats(sessions);

    // Initialiser les gestionnaires de scroll
    setTimeout(() => {
        window.SessionsManager.updateScrollIndicators();
    }, 100);
}

/**
 * NOUVELLE FONCTION: Fonction de recherche/filtrage des sessions
 */
function filterSessions(searchTerm) {
    if (!searchTerm || searchTerm.trim() === '') {
        // Réafficher toutes les sessions
        displaySessionsOptimized(window.SessionsManager.allSessions);
        return;
    }

    const filtered = window.SessionsManager.allSessions.filter(session =>
        session.toLowerCase().includes(searchTerm.toLowerCase())
    );

    displaySessionsOptimized(filtered);

    if (window.showToast) {
        window.showToast(
            `🔍 ${filtered.length} session(s) trouvée(s) pour "${searchTerm}"`,
            'info',
            3000
        );
    }
}

/**
 * NOUVELLE FONCTION: Fonction updateSessionsStats avec calculs plus précis
 */
function updateSessionsStats(sessions) {
    const totalSessionsEl = document.getElementById('totalSessions');
    const totalSizeEl = document.getElementById('totalSize');
    const sessionsCounterEl = document.getElementById('sessionsCounter');

    if (totalSessionsEl) {
        totalSessionsEl.textContent = sessions.length;
    }

    if (sessionsCounterEl) {
        const displayText = sessions.length === 0
            ? 'Aucune session'
            : `${sessions.length} session${sessions.length > 1 ? 's' : ''}`;
        sessionsCounterEl.textContent = displayText;
    }

    // Estimation de la taille plus réaliste
    if (totalSizeEl) {
        let estimatedSize;
        if (sessions.length === 0) {
            estimatedSize = 0;
        } else if (sessions.length < 10) {
            estimatedSize = sessions.length * 0.3; // ~300KB par session pour petites listes
        } else if (sessions.length < 100) {
            estimatedSize = sessions.length * 0.5; // ~500KB par session
        } else {
            estimatedSize = sessions.length * 0.4; // ~400KB par session (compression pour grandes listes)
        }

        if (estimatedSize < 1) {
            totalSizeEl.textContent = (estimatedSize * 1000).toFixed(0) + ' KB';
        } else {
            totalSizeEl.textContent = estimatedSize.toFixed(1) + ' MB';
        }
    }

    // Animation des statistiques
    [totalSessionsEl, totalSizeEl].forEach(el => {
        if (el) {
            el.style.transform = 'scale(1.1)';
            el.style.transition = 'transform 0.2s ease';
            setTimeout(() => {
                el.style.transform = 'scale(1)';
            }, 200);
        }
    });
}

/**
 * Charge la liste des sessions
 */
async function loadSessions() {
    try {
        const response = await fetch('/sessions');
        const data = await response.json();
        displaySessionsOptimized(data.sessions || []);
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
 * FONCTION MAINTENUE POUR COMPATIBILITÉ: Affiche les sessions (version simplifiée)
 */
function displaySessions(sessions) {
    // Appeler la version optimisée
    displaySessionsOptimized(sessions);
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

            if (validation === 'biological_data_confirmed_v2') {
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
 * Fonction pour activer/désactiver le mode debug
 */
function toggleDebugMode() {
    window.AppState.debugMode = !window.AppState.debugMode;
    showToast(
        `🔧 Mode debug ${window.AppState.debugMode ? 'activé' : 'désactivé'}`,
        'info',
        2000
    );
    console.log(`Debug mode: ${window.AppState.debugMode}`);
}

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

// Gestionnaire de clavier pour la recherche rapide et raccourcis
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + F pour ouvrir une recherche rapide de sessions
    if ((e.ctrlKey || e.metaKey) && e.key === 'f' && window.SessionsManager.allSessions.length > 0) {
        e.preventDefault();

        const searchTerm = prompt('🔍 Rechercher dans les sessions:', '');
        if (searchTerm !== null) {
            filterSessions(searchTerm);
        }
    }

    // Ctrl/Cmd + D pour le mode debug
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        toggleDebugMode();
    }

    // Raccourcis clavier existants
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case 'k':
                e.preventDefault();
                if (window.AppState.isConnected) {
                    disconnectDevice();
                } else {
                    connectDevice();
                }
                break;
            case 'r':
                e.preventDefault();
                if (window.AppState.isConnected) {
                    toggleRecording();
                }
                break;
        }
    }
});

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
window.disconnectDevice = disconnectDevice;
window.toggleRecording = toggleRecording;
window.downloadData = downloadData;
window.loadSessions = loadSessions;
window.displaySessions = displaySessions;
window.displaySessionsOptimized = displaySessionsOptimized;
window.updateSystemStatus = updateSystemStatus;
window.updateSessionsStats = updateSessionsStats;
window.filterSessions = filterSessions;
window.showToast = showToast;
window.startMonitoring = startMonitoring;
window.stopMonitoring = stopMonitoring;
window.toggleDebugMode = toggleDebugMode;
window.refreshSessions = refreshSessions;

console.log('✅ Application Neurosity Monitor chargée complètement avec Sessions Manager optimisé pour milliers de fichiers');