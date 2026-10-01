/**
 * NEUROSITY SETTINGS - JAVASCRIPT
 */

// ===============================================
// ÉTAT ET CONFIGURATION
// ===============================================

const SettingsApp = {
    currentConfig: null,
    isLoading: false
};

// ===============================================
// UTILITAIRES
// ===============================================

function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️'
    };

    toast.innerHTML = `
        <span style="font-size: 1.2rem;">${icons[type] || icons.info}</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    if (duration > 0) {
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

/**
 * Contenu de bouton traduisible : rendu immédiat + clé pour la retraduction.
 */
function btnContent(icon, key) {
    return `<span class="btn-icon">${icon}</span><span class="btn-text" data-i18n="${key}">${t(key)}</span>`;
}

function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('statusMessage');
    const statusText = document.getElementById('statusText');

    statusEl.className = `status-message ${type}`;
    statusText.textContent = message;
    statusEl.style.display = 'block';

    setTimeout(() => {
        statusEl.style.display = 'none';
    }, 5000);
}

function setLoading(isLoading) {
    SettingsApp.isLoading = isLoading;

    const saveBtn = document.getElementById('saveBtn');
    const testBtn = document.getElementById('testConnectionBtn');

    if (isLoading) {
        saveBtn.disabled = true;
        testBtn.disabled = true;
        saveBtn.innerHTML = btnContent('⏳', 'settings.saving');
    } else {
        saveBtn.disabled = false;
        testBtn.disabled = false;
        saveBtn.innerHTML = btnContent('💾', 'settings.save');
    }
}

// ===============================================
// API CALLS
// ===============================================

async function loadCurrentConfig() {
    try {
        const response = await fetch('/api/settings/current');
        const data = await response.json();

        if (data.success) {
            SettingsApp.currentConfig = data.config;
            displayCurrentConfig(data.config);
        }
    } catch (error) {
        console.error('Erreur chargement config:', error);
    }
}

async function saveConfiguration(formData) {
    try {
        setLoading(true);

        const response = await fetch('/api/settings/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            showToast(t('settings.toast.saved'), 'success');

            // Rediriger vers l'application après 1.5s
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            const message = I18n.fromServer(data, 'settings.toast.saveError');
            showToast(message, 'error');
            showStatus(message, 'error');
        }
    } catch (error) {
        console.error('Erreur sauvegarde:', error);
        showToast(t('settings.toast.serverError'), 'error');
        showStatus(t('settings.toast.serverError'), 'error');
    } finally {
        setLoading(false);
    }
}

async function testConnection() {
    const deviceId = document.getElementById('deviceId').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!deviceId || !email || !password) {
        showToast(t('settings.toast.fillAll'), 'error');
        return;
    }

    try {
        const testBtn = document.getElementById('testConnectionBtn');
        testBtn.disabled = true;
        testBtn.innerHTML = btnContent('🔄', 'settings.testing');

        showStatus(t('settings.toast.testing'), 'info');

        const response = await fetch('/api/settings/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                device_id: deviceId,
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast(t('settings.toast.testSuccess'), 'success');
            showStatus(t('settings.toast.testSuccessDetail'), 'success');
        } else {
            showToast(t('settings.toast.testFailed'), 'error');
            showStatus(`❌ ${I18n.fromServer(data, 'settings.toast.invalidCredentials')}`, 'error');
        }
    } catch (error) {
        console.error('Erreur test connexion:', error);
        showToast(t('settings.toast.testError'), 'error');
        showStatus(t('settings.toast.testErrorDetail'), 'error');
    } finally {
        const testBtn = document.getElementById('testConnectionBtn');
        testBtn.disabled = false;
        testBtn.innerHTML = btnContent('🔍', 'settings.test');
    }
}

async function clearConfiguration() {
    if (!confirm(t('settings.confirm.clear'))) {
        return;
    }

    try {
        const response = await fetch('/api/settings/clear', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showToast(t('settings.toast.cleared'), 'success');

            // Réinitialiser le formulaire
            document.getElementById('settingsForm').reset();
            document.getElementById('currentConfigSection').style.display = 'none';
        } else {
            showToast(t('settings.toast.clearError'), 'error');
        }
    } catch (error) {
        console.error('Erreur suppression config:', error);
        showToast(t('settings.toast.connectionError'), 'error');
    }
}

// ===============================================
// AFFICHAGE
// ===============================================

function displayCurrentConfig(config) {
    if (!config || !config.email) {
        return;
    }

    const section = document.getElementById('currentConfigSection');
    const emailEl = document.getElementById('currentEmail');
    const deviceIdEl = document.getElementById('currentDeviceId');

    emailEl.textContent = config.email || '-';

    // Afficher le Device ID tronqué
    if (config.device_id) {
        const truncated = config.device_id.substring(0, 12) + '...';
        deviceIdEl.textContent = truncated;
    } else {
        deviceIdEl.textContent = '-';
    }

    section.style.display = 'block';

    // Pré-remplir le formulaire (sauf le mot de passe)
    document.getElementById('deviceId').value = config.device_id || '';
    document.getElementById('email').value = config.email || '';
    document.getElementById('autoConnect').checked = config.auto_connect || false;
    document.getElementById('rememberCredentials').checked = config.remember_credentials !== false;
}

// ===============================================
// GESTION DU FORMULAIRE
// ===============================================

function handleFormSubmit(event) {
    event.preventDefault();

    const formData = {
        device_id: document.getElementById('deviceId').value.trim(),
        email: document.getElementById('email').value.trim(),
        password: document.getElementById('password').value,
        auto_connect: document.getElementById('autoConnect').checked,
        remember_credentials: document.getElementById('rememberCredentials').checked
    };

    // Validation
    if (!formData.device_id || !formData.email || !formData.password) {
        showToast(t('settings.toast.fillRequired'), 'error');
        return;
    }

    // Validation email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
        showToast(t('settings.toast.invalidEmail'), 'error');
        return;
    }

    // Validation Device ID (format basique)
    if (formData.device_id.length < 10) {
        showToast(t('settings.toast.deviceIdShort'), 'error');
        return;
    }

    saveConfiguration(formData);
}

// ===============================================
// EVENT LISTENERS
// ===============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🔧 Initialisation Settings...');

    // Charger la config actuelle
    loadCurrentConfig();

    // Formulaire
    document.getElementById('settingsForm').addEventListener('submit', handleFormSubmit);

    // Toggle mot de passe
    document.getElementById('togglePassword').addEventListener('click', () => {
        const passwordInput = document.getElementById('password');
        const toggleBtn = document.getElementById('togglePassword');

        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            toggleBtn.textContent = '🙈';
        } else {
            passwordInput.type = 'password';
            toggleBtn.textContent = '👁️';
        }
    });

    // Test connexion
    document.getElementById('testConnectionBtn').addEventListener('click', testConnection);

    // Retour app
    document.getElementById('backToApp').addEventListener('click', () => {
        window.location.href = '/';
    });

    // Effacer config
    document.getElementById('clearConfig').addEventListener('click', clearConfiguration);

    // Retour de la langue : confirmation visuelle
    I18n.onChange(() => showToast(t('toast.langChanged'), 'info', 2000));

    // Message de bienvenue
    showToast(t('settings.toast.welcome'), 'info', 5000);
});

// Raccourcis clavier
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + S pour sauvegarder
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        document.getElementById('settingsForm').dispatchEvent(new Event('submit'));
    }

    // Escape pour retourner
    if (e.key === 'Escape') {
        window.location.href = '/';
    }
});