/**
 * CSV VIEWER - Visualisation avancée des données Neurosity
 * Version avec filtrage temporel et sauvegarde de graphiques
 */

// ===============================================
// CONFIGURATION GLOBALE
// ===============================================

// Configuration globale Chart.js
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = '#64748b';
Chart.defaults.animation.duration = 750;

// Couleurs cohérentes
const COLORS = {
    delta: '#8b5cf6',
    theta: '#3b82f6',
    alpha: '#10b981',
    beta: '#f59e0b',
    gamma: '#ef4444',
    calm: '#6366f1',
    focus: '#10b981',
    electrodes: [
        '#ef4444', '#f59e0b', '#10b981', '#3b82f6',
        '#6366f1', '#8b5cf6', '#ec4899', '#14b8a6'
    ]
};

// Récupérer le nom du fichier depuis l'URL
const urlParams = new URLSearchParams(window.location.search);
const filename = urlParams.get('file');

// Variables globales
let analysisData = null;
let charts = {};
let filteredData = null; // Données filtrées
let currentFilter = { t1: null, t2: null }; // Filtre actuel

// ===============================================
// INITIALISATION
// ===============================================

document.addEventListener('DOMContentLoaded', async () => {
    if (!filename) {
        showError(t('viewer.error.noFile'));
        return;
    }

    document.getElementById('filename').textContent = t('viewer.file', { name: filename });

    // Retraduire toute la page (y compris les graphiques) au changement de langue
    I18n.onChange(applyLanguageToViewer);

    try {
        await loadAndVisualize();
    } catch (error) {
        console.error('Erreur:', error);
        showError(error.message);
    }
});

/**
 * Rejoue tout le rendu dynamique du visualiseur dans la nouvelle langue :
 * en-tête, informations de filtrage et l'intégralité des graphiques.
 */
function applyLanguageToViewer() {
    if (filename) {
        document.getElementById('filename').textContent = t('viewer.file', { name: filename });
    }

    if (!analysisData) return;

    initializeFilterLimits();
    updateFilterInfo(currentFilter.t1, currentFilter.t2);
    updateAllCharts();
}

// ===============================================
// CHARGEMENT DES DONNÉES
// ===============================================

async function loadAndVisualize() {
    try {
        const response = await fetch(`/api/analyze_csv/${filename}`);
        const payload = await response.json().catch(() => null);

        if (!response.ok) {
            throw new Error(
                payload
                    ? I18n.fromServer(payload, 'viewer.error')
                    : t('viewer.error.server', { status: response.status })
            );
        }

        analysisData = payload;

        if (analysisData.error) {
            throw new Error(I18n.fromServer(analysisData, 'viewer.error'));
        }

        console.log('Données chargées:', analysisData);

        // Initialiser les données filtrées avec toutes les données
        filteredData = analysisData;

        // Masquer le loading, afficher les charts
        document.getElementById('loading').style.display = 'none';
        document.getElementById('charts-container').style.display = 'block';

        // Mettre à jour les infos
        updateHeader();

        // Initialiser les limites du filtre
        initializeFilterLimits();

        // Créer tous les graphiques
        createAllCharts();

    } catch (error) {
        throw error;
    }
}

// ===============================================
// FILTRAGE TEMPOREL
// ===============================================

/**
 * Initialise les limites min/max des inputs de filtrage
 */
function initializeFilterLimits() {
    const duration = analysisData.duration || 0;
    const t2Input = document.getElementById('t2Input');

    t2Input.setAttribute('max', Math.ceil(duration));
    t2Input.placeholder = duration > 0 ? Math.ceil(duration) : t('filter.t2.placeholder');
}

/**
 * Applique le filtre temporel
 */
function applyTimeFilter() {
    const t1 = parseFloat(document.getElementById('t1Input').value) || 0;
    const t2 = parseFloat(document.getElementById('t2Input').value) || analysisData.duration;

    // Validation
    if (t1 < 0) {
        showToast(t('filter.error.t1'), 'error');
        return;
    }

    if (t2 <= t1) {
        showToast(t('filter.error.t2'), 'error');
        return;
    }

    if (t2 > analysisData.duration) {
        showToast(t('filter.warn.t2'), 'info');
        document.getElementById('t2Input').value = Math.ceil(analysisData.duration);
    }

    // Appliquer le filtre
    currentFilter = { t1, t2 };
    filteredData = filterDataByTime(analysisData, t1, t2);

    // Mettre à jour l'interface
    updateFilterInfo(t1, t2);
    updateAllCharts();

    showToast(t('filter.applied'), 'success');
}

/**
 * Réinitialise le filtre temporel
 */
function resetTimeFilter() {
    currentFilter = { t1: null, t2: null };
    filteredData = analysisData;

    document.getElementById('t1Input').value = '';
    document.getElementById('t2Input').value = '';

    updateFilterInfo(null, null);
    updateAllCharts();

    showToast(t('filter.wasReset'), 'info');
}

/**
 * Filtre les données par période temporelle
 */
function filterDataByTime(data, t1, t2) {
    const filtered = {
        ...data,
        timestamps: [],
        cognitive_states: {
            calm: [],
            focus: []
        },
        frequency_bands: {
            delta: {},
            theta: {},
            alpha: {},
            beta: {},
            gamma: {}
        },
        eeg_raw: {},
        derived_metrics: {}
    };

    // Initialiser les structures
    const electrodes = ['CP3', 'C3', 'F5', 'PO3', 'PO4', 'F6', 'C4', 'CP4'];
    for (const band of ['delta', 'theta', 'alpha', 'beta', 'gamma']) {
        for (const electrode of electrodes) {
            filtered.frequency_bands[band][electrode] = [];
        }
    }

    for (const electrode of electrodes) {
        filtered.eeg_raw[electrode] = [];
    }

    // Copier les structures de métriques dérivées
    for (const metric in data.derived_metrics) {
        filtered.derived_metrics[metric] = [];
    }

    // Convertir les timestamps en secondes relatives
    const firstTimestamp = new Date(data.timestamps[0]).getTime();

    data.timestamps.forEach((timestamp, idx) => {
        const currentTime = (new Date(timestamp).getTime() - firstTimestamp) / 1000;

        // Vérifier si le point est dans la plage
        if (currentTime >= t1 && currentTime <= t2) {
            filtered.timestamps.push(timestamp);

            // États cognitifs
            if (data.cognitive_states.calm[idx] !== undefined) {
                filtered.cognitive_states.calm.push(data.cognitive_states.calm[idx]);
            }
            if (data.cognitive_states.focus[idx] !== undefined) {
                filtered.cognitive_states.focus.push(data.cognitive_states.focus[idx]);
            }

            // Bandes de fréquences
            for (const band of ['delta', 'theta', 'alpha', 'beta', 'gamma']) {
                for (const electrode of electrodes) {
                    if (data.frequency_bands[band][electrode][idx] !== undefined) {
                        filtered.frequency_bands[band][electrode].push(
                            data.frequency_bands[band][electrode][idx]
                        );
                    }
                }
            }

            // EEG brut
            for (const electrode of electrodes) {
                if (data.eeg_raw[electrode][idx] !== undefined) {
                    filtered.eeg_raw[electrode].push(data.eeg_raw[electrode][idx]);
                }
            }

            // Métriques dérivées
            for (const metric in data.derived_metrics) {
                if (data.derived_metrics[metric][idx] !== undefined) {
                    filtered.derived_metrics[metric].push(data.derived_metrics[metric][idx]);
                }
            }
        }
    });

    filtered.total_points = filtered.timestamps.length;
    filtered.duration = t2 - t1;

    return filtered;
}

/**
 * Met à jour l'affichage des informations de filtrage
 */
function updateFilterInfo(t1, t2) {
    const filterInfo = document.getElementById('filterInfo');

    if (t1 !== null && t2 !== null) {
        filterInfo.className = 'filter-info active';
        filterInfo.removeAttribute('data-i18n');
        filterInfo.innerHTML = t('filter.active', {
            t1: t1,
            t2: t2,
            duration: (t2 - t1).toFixed(1),
            points: filteredData.total_points
        });
    } else {
        filterInfo.className = 'filter-info';
        filterInfo.setAttribute('data-i18n', 'filter.none');
        filterInfo.textContent = t('filter.none');
    }
}

// ===============================================
// SAUVEGARDE DES GRAPHIQUES
// ===============================================

/**
 * Sauvegarde un graphique en PNG
 */
function saveChart(chartId, nameKey) {
    const canvas = document.getElementById(chartId);
    if (!canvas) {
        showToast(t('viewer.chartNotFound'), 'error');
        return;
    }

    try {
        // Le nom du fichier suit la langue de l'interface
        let fullFilename = t(nameKey);
        if (currentFilter.t1 !== null && currentFilter.t2 !== null) {
            fullFilename += `_${currentFilter.t1}s-${currentFilter.t2}s`;
        }
        fullFilename += '.png';

        // Créer un lien de téléchargement
        canvas.toBlob((blob) => {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.download = fullFilename;
            link.href = url;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            showToast(t('viewer.saved', { file: fullFilename }), 'success');
        });
    } catch (error) {
        console.error('Erreur sauvegarde:', error);
        showToast(t('viewer.saveError'), 'error');
    }
}

// ===============================================
// MISE À JOUR DU HEADER
// ===============================================

function updateHeader() {
    const data = filteredData || analysisData;
    const duration = data.duration || 0;
    const minutes = Math.floor(duration / 60);
    const seconds = Math.floor(duration % 60);

    document.getElementById('duration').textContent = t('viewer.durationValue', { m: minutes, s: seconds });
    document.getElementById('points').textContent = I18n.formatNumber(data.total_points || 0);
}

// ===============================================
// CRÉATION DES GRAPHIQUES
// ===============================================

function createAllCharts() {
    createCognitiveStatesChart();
    createFrequencyBandsChart();
    createDeltaBetaRatioChart();
    createCognitiveLoadChart();
    createRatiosChart();
    createDerivedMetricsChart();
    createAsymmetriesChart();
    createEEGRawChart();
    createRelativePowersChart();
    if (typeof initReplayUI === 'function') {
        initReplayUI();
    }
}

/**
 * Met à jour tous les graphiques avec les données filtrées
 */
function updateAllCharts() {
    updateHeader();

    // Détruire et recréer les graphiques
    for (const chartId in charts) {
        if (charts[chartId]) {
            charts[chartId].destroy();
        }
    }
    charts = {};

    createAllCharts();
}

// ===============================================
// GRAPHIQUE 1: ÉTATS COGNITIFS
// ===============================================

function createCognitiveStatesChart() {
    const ctx = document.getElementById('cognitiveStatesChart');
    if (!ctx) return;

    const data = filteredData || analysisData;
    const timestamps = formatTimestamps(data.timestamps);
    const calmData = data.cognitive_states.calm;
    const focusData = data.cognitive_states.focus;

    charts.cognitiveStates = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [
                {
                    label: t('series.calm'),
                    data: calmData,
                    borderColor: COLORS.calm,
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.focus'),
                    data: focusData,
                    borderColor: COLORS.focus,
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            return value !== null
                                ? `${context.dataset.label}: ${value.toFixed(1)}%`
                                : `${context.dataset.label}: ${t('tooltip.na')}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: t('axis.probability')
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: t('axis.time')
                    },
                    ticks: {
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ===============================================
// GRAPHIQUE 2: BANDES DE FRÉQUENCES
// ===============================================

function createFrequencyBandsChart() {
    const ctx = document.getElementById('frequencyBandsChart');
    if (!ctx) return;

    const data = filteredData || analysisData;
    const timestamps = formatTimestamps(data.timestamps);
    const bands = data.frequency_bands;

    const datasets = [
        {
            label: t('series.delta'),
            data: calculateBandAverage(bands.delta),
            borderColor: COLORS.delta,
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            pointRadius: 0,
            pointHoverRadius: 4
        },
        {
            label: t('series.theta'),
            data: calculateBandAverage(bands.theta),
            borderColor: COLORS.theta,
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            pointRadius: 0,
            pointHoverRadius: 4
        },
        {
            label: t('series.alpha'),
            data: calculateBandAverage(bands.alpha),
            borderColor: COLORS.alpha,
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            pointRadius: 0,
            pointHoverRadius: 4
        },
        {
            label: t('series.beta'),
            data: calculateBandAverage(bands.beta),
            borderColor: COLORS.beta,
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            pointRadius: 0,
            pointHoverRadius: 4
        },
        {
            label: t('series.gamma'),
            data: calculateBandAverage(bands.gamma),
            borderColor: COLORS.gamma,
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            pointRadius: 0,
            pointHoverRadius: 4
        }
    ];

    charts.frequencyBands = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            return value !== null
                                ? `${context.dataset.label}: ${value.toFixed(3)} µV²`
                                : `${context.dataset.label}: ${t('tooltip.na')}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 30,
                    title: {
                        display: true,
                        text: t('axis.power')
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: t('axis.time')
                    },
                    ticks: {
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}





// ===============================================
// GRAPHIQUE 3: CHARGE AFFECTIVE (DELTA/BETA)
// ===============================================

function createDeltaBetaRatioChart() {
    const ctx = document.getElementById('deltaBetaRatioChart');
    if (!ctx) return;

    const data = filteredData || analysisData;
    const timestamps = formatTimestamps(data.timestamps);
    const metrics = data.derived_metrics;

    charts.deltaBetaRatio = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [
                {
                    label: t('series.deltaBeta'),
                    data: metrics.delta_beta_ratio,
                    borderColor: '#e11d48',
                    backgroundColor: 'rgba(225, 29, 72, 0.1)',
                    borderWidth: 2.5,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            const label = context.dataset.label;
                            if (value === null) return `${label}: ${t('tooltip.na')}`;
                            let state = '';
                            if (value > 3) state = t('tooltip.drowsiness');
                            else if (value > 1.5) state = t('tooltip.relaxation');
                            else state = t('tooltip.activeWake');
                            return `${label}: ${value.toFixed(3)}${state}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: t('axis.deltaBetaRatio')
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: t('axis.time')
                    },
                    ticks: {
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ===============================================
// GRAPHIQUE 3b: CHARGE COGNITIVE (THETA/ALPHA)
// ===============================================

function createCognitiveLoadChart() {
    const ctx = document.getElementById('cognitiveLoadChart');
    if (!ctx) return;

    const data = filteredData || analysisData;
    const timestamps = formatTimestamps(data.timestamps);
    const metrics = data.derived_metrics;

    charts.cognitiveLoad = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [
                {
                    label: t('series.cognitiveLoad'),
                    data: metrics.cognitive_load,
                    borderColor: COLORS.theta,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2.5,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            return value !== null
                                ? `${context.dataset.label}: ${value.toFixed(3)}`
                                : `${context.dataset.label}: ${t('tooltip.na')}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: t('axis.thetaAlphaRatio')
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: t('axis.time')
                    },
                    ticks: {
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ===============================================
// GRAPHIQUE 4: RATIOS COGNITIFS
// ===============================================

function createRatiosChart() {
    const ctx = document.getElementById('ratiosChart');
    if (!ctx) return;

    const data = filteredData || analysisData;
    const timestamps = formatTimestamps(data.timestamps);
    const metrics = data.derived_metrics;

    charts.ratios = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [
                {
                    label: t('series.thetaBeta'),
                    data: metrics.theta_beta_ratio,
                    borderColor: COLORS.theta,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.alphaTheta'),
                    data: metrics.alpha_theta_ratio,
                    borderColor: COLORS.alpha,
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.betaAlpha'),
                    data: metrics.beta_alpha_ratio,
                    borderColor: COLORS.beta,
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.deltaBeta'),
                    data: metrics.delta_beta_ratio,
                    borderColor: '#e11d48',
                    backgroundColor: 'rgba(225, 29, 72, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.slowing'),
                    data: metrics.activation_level,
                    borderColor: COLORS.calm,
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            return value !== null
                                ? `${context.dataset.label}: ${value.toFixed(3)}`
                                : `${context.dataset.label}: ${t('tooltip.na')}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: t('axis.ratio')
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: t('axis.time')
                    },
                    ticks: {
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ===============================================
// GRAPHIQUE 5: MÉTRIQUES DÉRIVÉES
// ===============================================

function createDerivedMetricsChart() {
    const ctx = document.getElementById('derivedMetricsChart');
    if (!ctx) return;

    const data = filteredData || analysisData;
    const timestamps = formatTimestamps(data.timestamps);
    const metrics = data.derived_metrics;

    charts.derivedMetrics = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [
                {
                    label: t('series.engagement'),
                    data: metrics.engagement,
                    borderColor: COLORS.focus,
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.cognitiveLoad'),
                    data: metrics.cognitive_load,
                    borderColor: COLORS.theta,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.relaxation'),
                    data: metrics.relaxation,
                    borderColor: COLORS.calm,
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            return value !== null
                                ? `${context.dataset.label}: ${value.toFixed(3)}`
                                : `${context.dataset.label}: ${t('tooltip.na')}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: t('axis.normalized')
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: t('axis.time')
                    },
                    ticks: {
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ===============================================
// GRAPHIQUE 6: ASYMÉTRIES EEG
// ===============================================

function createAsymmetriesChart() {
    const ctx = document.getElementById('asymmetriesChart');
    if (!ctx) return;

    const data = filteredData || analysisData;
    const timestamps = formatTimestamps(data.timestamps);
    const metrics = data.derived_metrics;

    charts.asymmetries = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [
                {
                    label: t('series.asymFrontal'),
                    data: metrics.asymmetry_frontal,
                    borderColor: COLORS.calm,
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.asymCentral'),
                    data: metrics.asymmetry_central,
                    borderColor: COLORS.alpha,
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.asymParietal'),
                    data: metrics.asymmetry_parietal,
                    borderColor: COLORS.beta,
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            return value !== null
                                ? `${context.dataset.label}: ${value.toFixed(3)}`
                                : `${context.dataset.label}: ${t('tooltip.na')}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: t('axis.asymmetry')
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: t('axis.time')
                    },
                    ticks: {
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}


// Nouveau graphique : Puissances relatives
function createRelativePowersChart() {
    const ctx = document.getElementById('relativePowersChart');
    if (!ctx) return;

    const data = filteredData || analysisData;
    const timestamps = formatTimestamps(data.timestamps);
    const metrics = data.derived_metrics;

    charts.relativePowers = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [
                {
                    label: t('series.deltaRelative'),
                    data: metrics.delta_relative,
                    borderColor: COLORS.delta,
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.thetaRelative'),
                    data: metrics.theta_relative,
                    borderColor: COLORS.theta,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.alphaRelative'),
                    data: metrics.alpha_relative,
                    borderColor: COLORS.alpha,
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.betaRelative'),
                    data: metrics.beta_relative,
                    borderColor: COLORS.beta,
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: t('series.gammaRelative'),
                    data: metrics.gamma_relative,
                    borderColor: COLORS.gamma,
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            return value !== null
                                ? `${context.dataset.label}: ${value.toFixed(1)}%`
                                : `${context.dataset.label}: ${t('tooltip.na')}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: t('axis.relativePower')
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: t('axis.time')
                    },
                    ticks: {
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ===============================================
// GRAPHIQUE 7: SIGNAUX EEG BRUTS
// ===============================================

function createEEGRawChart() {
    const ctx = document.getElementById('eegRawChart');
    if (!ctx) return;

    const data = filteredData || analysisData;
    const timestamps = formatTimestamps(data.timestamps);
    const eeg = data.eeg_raw;

    const electrodes = ['CP3', 'C3', 'F5', 'PO3', 'PO4', 'F6', 'C4', 'CP4'];

    const datasets = electrodes.map((electrode, idx) => ({
        label: electrode,
        data: eeg[electrode],
        borderColor: COLORS.electrodes[idx],
        backgroundColor: 'transparent',
        borderWidth: 1.5,
        tension: 0.2,
        pointRadius: 0,
        pointHoverRadius: 3
    }));

    charts.eegRaw = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'nearest',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            return value !== null
                                ? `${context.dataset.label}: ${value.toFixed(2)} µV`
                                : `${context.dataset.label}: ${t('tooltip.na')}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: t('axis.amplitude')
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: t('axis.time')
                    },
                    ticks: {
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ===============================================
// FONCTIONS UTILITAIRES
// ===============================================

/**
 * Formate les timestamps pour l'affichage
 */
function formatTimestamps(timestamps) {
    if (!timestamps || timestamps.length === 0) return [];

    // Toujours utiliser le premier timestamp global comme référence
    // pour que la loupe temporelle conserve la même échelle en minutes
    const globalStart = analysisData && analysisData.timestamps && analysisData.timestamps.length > 0
        ? new Date(analysisData.timestamps[0])
        : new Date(timestamps[0]);

    return timestamps.map((ts, idx) => {
        try {
            const date = new Date(ts);
            const seconds = Math.floor((date - globalStart) / 1000);
            const minutes = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        } catch (e) {
            return `T+${idx}`;
        }
    });
}

/**
 * Calcule la moyenne d'une bande sur toutes les électrodes
 */
function calculateBandAverage(bandData) {
    if (!bandData) return [];

    const electrodes = Object.keys(bandData);
    if (electrodes.length === 0) return [];

    const numPoints = bandData[electrodes[0]].length;
    const averages = [];

    for (let i = 0; i < numPoints; i++) {
        let sum = 0;
        let count = 0;

        electrodes.forEach(electrode => {
            const value = bandData[electrode][i];
            if (value !== null && value !== undefined && !isNaN(value)) {
                sum += value;
                count++;
            }
        });

        averages.push(count > 0 ? sum / count : null);
    }

    return averages;
}

/**
 * Affiche une notification toast
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span style="font-size: 1.2rem;">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
        <span>${message}</span>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Affiche une erreur
 */
function showError(message) {
    const errorDiv = document.getElementById('error');
    const loadingDiv = document.getElementById('loading');

    if (errorDiv) {
        errorDiv.innerHTML = `
            <div class="error">
                <strong>❌ ${t('viewer.error')}</strong><br>
                ${message}
                <br><br>
                <a href="/" style="color: #667eea; text-decoration: none; font-weight: 600;">${t('viewer.back')}</a>
            </div>
        `;
        errorDiv.style.display = 'block';
    }

    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

// ===============================================
// GESTION DES ERREURS GLOBALES
// ===============================================

window.addEventListener('error', (event) => {
    console.error('Erreur globale:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Promise rejetée:', event.reason);
});

// ===============================================
// REPLAY TEMPOREL + ZOOM VISUEL
// ===============================================

const replayState = {
    playing: false,
    currentIdx: 0,
    speed: 1,
    rafId: null,
    lastFrameMs: 0,
    accumulatedSec: 0,
    zoomMin: null,   // index de début de la fenêtre zoomée (null = pas de zoom)
    zoomMax: null    // index de fin
};

// ============ OVERLAY CANVAS POUR LE CURSEUR ============
// On dessine le curseur sur un canvas séparé positionné par-dessus chaque graphe.
// Cela évite de redessiner les datasets à chaque frame (gain ~20×).
const cursorOverlays = []; // [{chart, overlay, ctx}]

function setupCursorOverlays() {
    // Nettoyer les anciens overlays
    for (const entry of cursorOverlays) {
        if (entry.overlay && entry.overlay.parentElement) {
            entry.overlay.parentElement.removeChild(entry.overlay);
        }
    }
    cursorOverlays.length = 0;

    for (const id in charts) {
        const chart = charts[id];
        if (!chart || !chart.canvas) continue;
        const container = chart.canvas.parentElement;
        if (!container) continue;

        const overlay = document.createElement('canvas');
        overlay.className = 'replay-cursor-overlay';
        overlay.style.position = 'absolute';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.pointerEvents = 'none';
        container.appendChild(overlay);

        cursorOverlays.push({ chart, overlay, ctx: overlay.getContext('2d') });
    }
}

function syncOverlaySize(entry) {
    const c = entry.chart.canvas;
    if (!c) return;
    const dpr = window.devicePixelRatio || 1;
    const cssW = c.clientWidth;
    const cssH = c.clientHeight;
    const targetW = Math.round(cssW * dpr);
    const targetH = Math.round(cssH * dpr);
    if (entry.overlay.width !== targetW || entry.overlay.height !== targetH) {
        entry.overlay.width = targetW;
        entry.overlay.height = targetH;
    }
}

function drawAllCursors() {
    for (const entry of cursorOverlays) {
        const { chart, overlay, ctx } = entry;
        if (!chart || !chart.scales || !chart.scales.x) continue;

        syncOverlaySize(entry);
        const dpr = window.devicePixelRatio || 1;

        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, overlay.width, overlay.height);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        const xScale = chart.scales.x;
        const labels = chart.data.labels;
        if (!labels || labels.length === 0) continue;

        const idx = Math.min(replayState.currentIdx, labels.length - 1);
        const xPx = xScale.getPixelForValue(idx);
        if (xPx == null || isNaN(xPx)) continue;
        if (xPx < xScale.left - 1 || xPx > xScale.right + 1) continue;

        const area = chart.chartArea;
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.9)';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.moveTo(xPx, area.top);
        ctx.lineTo(xPx, area.bottom);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = 'rgba(239, 68, 68, 0.95)';
        ctx.beginPath();
        ctx.arc(xPx, area.top + 4, 4, 0, Math.PI * 2);
        ctx.fill();
    }
}

// Resynchroniser les overlays après resize de la fenêtre
window.addEventListener('resize', () => {
    requestAnimationFrame(drawAllCursors);
});

function getReplaySource() {
    return filteredData || analysisData;
}

function getReplayLength() {
    const d = getReplaySource();
    return d && d.timestamps ? d.timestamps.length : 0;
}

function getReplayTotalSec() {
    const d = getReplaySource();
    return d && typeof d.duration === 'number' ? d.duration : 0;
}

function formatSeconds(sec) {
    if (!isFinite(sec) || sec < 0) sec = 0;
    const m = Math.floor(sec / 60);
    const s = sec - m * 60;
    return m > 0 ? `${m}m ${s.toFixed(1)}s` : `${s.toFixed(1)} s`;
}

function idxToSec(idx) {
    const n = getReplayLength();
    if (n <= 1) return 0;
    return (idx / (n - 1)) * getReplayTotalSec();
}

function secToIdx(sec) {
    const n = getReplayLength();
    if (n <= 1) return 0;
    const total = getReplayTotalSec();
    if (total <= 0) return 0;
    return Math.max(0, Math.min(n - 1, Math.round((sec / total) * (n - 1))));
}

function updateReplayUI() {
    const n = getReplayLength();
    const total = getReplayTotalSec();
    const curSec = idxToSec(replayState.currentIdx);

    const curEl = document.getElementById('replayCurrentTime');
    const durEl = document.getElementById('replayDuration');
    const prog = document.getElementById('replayProgress');

    if (curEl) curEl.textContent = formatSeconds(curSec);
    if (durEl) durEl.textContent = formatSeconds(total);
    if (prog && n > 1) {
        prog.value = String(Math.round((replayState.currentIdx / (n - 1)) * 1000));
    }
}

function replayTick(tsMs) {
    if (!replayState.playing) return;
    if (replayState.lastFrameMs === 0) replayState.lastFrameMs = tsMs;

    const dt = (tsMs - replayState.lastFrameMs) / 1000;
    replayState.lastFrameMs = tsMs;
    replayState.accumulatedSec += dt * replayState.speed;

    const total = getReplayTotalSec();
    if (total <= 0) { pauseReplay(); return; }

    if (replayState.accumulatedSec >= total) {
        replayState.accumulatedSec = total;
        replayState.currentIdx = getReplayLength() - 1;
        updateReplayUI();
        drawAllCursors();
        pauseReplay();
        return;
    }

    replayState.currentIdx = secToIdx(replayState.accumulatedSec);
    updateReplayUI();
    drawAllCursors();

    replayState.rafId = requestAnimationFrame(replayTick);
}

function playReplay() {
    if (replayState.playing) return;
    const n = getReplayLength();
    if (n <= 1) return;

    // Si on est à la fin, on repart du début
    if (replayState.currentIdx >= n - 1) {
        replayState.currentIdx = 0;
        replayState.accumulatedSec = 0;
    }
    replayState.playing = true;
    replayState.lastFrameMs = 0;
    const btn = document.getElementById('replayPlayBtn');
    if (btn) btn.textContent = '⏸';
    replayState.rafId = requestAnimationFrame(replayTick);
}

function pauseReplay() {
    replayState.playing = false;
    if (replayState.rafId) {
        cancelAnimationFrame(replayState.rafId);
        replayState.rafId = null;
    }
    const btn = document.getElementById('replayPlayBtn');
    if (btn) btn.textContent = '▶';
}

function togglePlayPause() {
    if (replayState.playing) pauseReplay();
    else playReplay();
}

function stopReplay() {
    pauseReplay();
    replayState.currentIdx = 0;
    replayState.accumulatedSec = 0;
    updateReplayUI();
    drawAllCursors();
}

function seekReplayByProgress(pctValue) {
    const pct = Math.max(0, Math.min(1, pctValue / 1000));
    const total = getReplayTotalSec();
    replayState.accumulatedSec = pct * total;
    replayState.currentIdx = secToIdx(replayState.accumulatedSec);
    replayState.lastFrameMs = 0;
    updateReplayUI();
    drawAllCursors();
}

function setReplaySpeed(value) {
    const v = parseFloat(value);
    if (isFinite(v) && v > 0) replayState.speed = v;
}

// ============ ZOOM VISUEL ============

function applyZoomToCharts() {
    const n = getReplayLength();
    for (const id in charts) {
        const c = charts[id];
        if (!c || !c.options || !c.options.scales || !c.options.scales.x) continue;
        if (replayState.zoomMin !== null && replayState.zoomMax !== null && n > 1) {
            c.options.scales.x.min = Math.max(0, replayState.zoomMin);
            c.options.scales.x.max = Math.min(n - 1, replayState.zoomMax);
        } else {
            delete c.options.scales.x.min;
            delete c.options.scales.x.max;
        }
        c.update('none');
    }
    // Le curseur doit être redessiné après le re-rendu des scales
    requestAnimationFrame(drawAllCursors);
}

function resetZoom() {
    replayState.zoomMin = null;
    replayState.zoomMax = null;
    applyZoomToCharts();
}

// Zoom à la molette, centré sur la position du pointeur dans le graphe survolé.
// Tous les graphiques sont ensuite synchronisés sur la même fenêtre x.
function handleWheelZoom(chart, e) {
    if (!chart || !chart.scales || !chart.scales.x) return;
    const n = getReplayLength();
    if (n <= 4) return;

    e.preventDefault();

    const rect = chart.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const valueAtMouse = chart.scales.x.getValueForPixel(mouseX);
    if (valueAtMouse == null || isNaN(valueAtMouse)) return;
    const center = Math.max(0, Math.min(n - 1, valueAtMouse));

    const curMin = replayState.zoomMin !== null ? replayState.zoomMin : 0;
    const curMax = replayState.zoomMax !== null ? replayState.zoomMax : n - 1;
    const curWidth = Math.max(2, curMax - curMin);

    // deltaY > 0 = molette vers soi = zoom arrière
    const factor = e.deltaY > 0 ? 1.25 : 0.8;
    const newWidth = Math.max(4, Math.min(n - 1, Math.round(curWidth * factor)));

    // Préserve la position du pointeur dans la fenêtre (zoom "ancré")
    const ratio = (center - curMin) / curWidth;
    let newMin = Math.round(center - ratio * newWidth);
    let newMax = newMin + newWidth;
    if (newMin < 0) { newMin = 0; newMax = newWidth; }
    if (newMax > n - 1) { newMax = n - 1; newMin = Math.max(0, newMax - newWidth); }

    if (newMin <= 0 && newMax >= n - 1) {
        replayState.zoomMin = null;
        replayState.zoomMax = null;
    } else {
        replayState.zoomMin = newMin;
        replayState.zoomMax = newMax;
    }
    applyZoomToCharts();
}

function attachMouseZoomToCharts() {
    for (const id in charts) {
        const chart = charts[id];
        if (!chart || !chart.canvas) continue;
        const canvas = chart.canvas;

        // Les graphiques sont détruits/recréés (filtrage temporel, changement de
        // langue) : on mémorise la clé pour résoudre le graphique courant au
        // moment de l'événement plutôt que de capturer une instance périmée.
        canvas.dataset.chartKey = id;

        if (canvas._mouseZoomAttached) continue;
        canvas._mouseZoomAttached = true;

        canvas.addEventListener('wheel', (e) => {
            const current = charts[canvas.dataset.chartKey];
            if (current && current.canvas) handleWheelZoom(current, e);
        }, { passive: false });
        canvas.addEventListener('dblclick', () => resetZoom());
    }
}

// ============ INITIALISATION DU REPLAY ============

let replayInitialized = false;

function initReplayUI() {
    const panel = document.getElementById('replayPanel');
    if (panel) panel.style.display = 'block';

    if (!replayInitialized) {
        document.getElementById('replayPlayBtn').addEventListener('click', togglePlayPause);
        document.getElementById('replayStopBtn').addEventListener('click', stopReplay);
        document.getElementById('replayProgress').addEventListener('input', (e) => {
            if (replayState.playing) pauseReplay();
            seekReplayByProgress(parseFloat(e.target.value));
        });
        document.getElementById('replaySpeed').addEventListener('change', (e) => {
            setReplaySpeed(e.target.value);
        });

        // Raccourci clavier : espace = play/pause
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space'
                && e.target.tagName !== 'INPUT'
                && e.target.tagName !== 'SELECT'
                && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                togglePlayPause();
            }
        });

        replayInitialized = true;
    }

    // Réinitialiser l'état à chaque (re)chargement / filtrage
    pauseReplay();
    replayState.currentIdx = 0;
    replayState.accumulatedSec = 0;
    replayState.zoomMin = null;
    replayState.zoomMax = null;

    // (Re)créer les overlays et brancher la molette sur les graphes fraîchement rendus
    setupCursorOverlays();
    attachMouseZoomToCharts();

    updateReplayUI();
    // Premier dessin du curseur à l'index 0
    requestAnimationFrame(drawAllCursors);
}

// Log de débogage
console.log('CSV Viewer Enhanced initialisé (avec replay + zoom)');
console.log('Fichier à analyser:', filename);