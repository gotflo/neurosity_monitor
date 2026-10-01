#!/usr/bin/env python3
"""
Traductions côté serveur pour Neurosity Monitor.

Le serveur ne rend que des messages courts (réponses d'API, messages
console). L'interface complète est traduite côté client par static/js/i18n.js.

Chaque réponse d'API renvoie en plus un `code` stable : le client peut ainsi
traduire lui-même le message quelle que soit la langue du cookie.
"""

from typing import Optional

DEFAULT_LANG = 'fr'
SUPPORTED_LANGS = ('fr', 'en')
LANG_COOKIE = 'neuro_lang'

TRANSLATIONS = {
    'fr': {
        'missing_config': 'Configuration manquante. Allez dans Configuration.',
        'device_not_detected': "Casque non détecté. Vérifiez qu'il est allumé et porté correctement.",
        'device_connected': 'Casque Neurosity connecté !',
        'not_connected': 'Non connecté',
        'module_not_ready': 'Module non initialisé',
        'sdk_missing': 'SDK Neurosity non installé. Installez-le avec : pip install neurosity',
        'config_saved': 'Configuration sauvegardée',
        'save_failed': 'Erreur de sauvegarde',
        'config_cleared': 'Configuration effacée',
        'test_success': 'Connexion réussie !',
        'file_not_found': 'Fichier non trouvé',
        'empty_csv': 'Fichier CSV vide',
        'error': 'Erreur',
        'language_saved': 'Langue enregistrée',
        'unsupported_language': 'Langue non supportée',
        # Messages console
        'console.ready': 'Serveur prêt',
        'console.settings': 'Configuration',
        'console.instructions': 'Instructions',
        'console.step1': 'Configurez vos identifiants sur /settings',
        'console.step2': 'Allumez votre casque Neurosity Crown',
        'console.step3': 'Portez-le correctement',
        'console.step4': "Cliquez sur « Connecter »",
        'console.step5': 'Observez vos ondes cérébrales !',
    },
    'en': {
        'missing_config': 'Missing configuration. Go to Settings.',
        'device_not_detected': 'Headset not detected. Make sure it is turned on and correctly worn.',
        'device_connected': 'Neurosity headset connected!',
        'not_connected': 'Not connected',
        'module_not_ready': 'Module not initialized',
        'sdk_missing': 'Neurosity SDK not installed. Install it with: pip install neurosity',
        'config_saved': 'Configuration saved',
        'save_failed': 'Save error',
        'config_cleared': 'Configuration cleared',
        'test_success': 'Connection successful!',
        'file_not_found': 'File not found',
        'empty_csv': 'Empty CSV file',
        'error': 'Error',
        'language_saved': 'Language saved',
        'unsupported_language': 'Unsupported language',
        # Console messages
        'console.ready': 'Server ready',
        'console.settings': 'Settings',
        'console.instructions': 'Instructions',
        'console.step1': 'Set up your credentials on /settings',
        'console.step2': 'Turn on your Neurosity Crown headset',
        'console.step3': 'Wear it properly',
        'console.step4': 'Click "Connect"',
        'console.step5': 'Watch your brainwaves!',
    },
}


def normalize_lang(lang: Optional[str]) -> str:
    """Ramène une valeur quelconque à une langue supportée."""
    if not lang:
        return DEFAULT_LANG
    short = str(lang).strip().lower()[:2]
    return short if short in SUPPORTED_LANGS else DEFAULT_LANG


def get_locale() -> str:
    """Langue de la requête courante (cookie), FR par défaut."""
    try:
        from flask import request, has_request_context
        if has_request_context():
            return normalize_lang(request.cookies.get(LANG_COOKIE))
    except Exception:
        pass
    return DEFAULT_LANG


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """Traduit une clé dans la langue demandée (ou celle de la requête)."""
    language = normalize_lang(lang) if lang else get_locale()
    table = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANG])
    value = table.get(key, TRANSLATIONS[DEFAULT_LANG].get(key, key))
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return value


def message(code: str, lang: Optional[str] = None, **kwargs) -> dict:
    """Construit la partie message d'une réponse JSON : texte + code stable."""
    return {'message': t(code, lang, **kwargs), 'code': code}


def error(code: str, lang: Optional[str] = None, **kwargs) -> dict:
    """Construit la partie erreur d'une réponse JSON : texte + code stable."""
    return {'error': t(code, lang, **kwargs), 'code': code}


def register_i18n(app):
    """Expose `lang` et `t` aux templates Jinja."""

    @app.context_processor
    def inject_i18n():
        return {'lang': get_locale(), 't': t}

    return app
