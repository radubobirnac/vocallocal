/**
 * Language Preferences Manager
 * Handles cookie-based language persistence across all features
 * Provides better mobile UX by remembering user language choices
 */

class LanguagePreferences {
  constructor() {
    this.cookiePrefix = 'vocallocal_lang_';
    this.cookieOptions = {
      expires: 365, // 1 year
      path: '/',
      sameSite: 'Lax'
    };
    
    // Language preference keys
    this.preferences = {
      source: 'source_language',
      target: 'target_language',
      transcription: 'transcription_language',
      translation_from: 'translation_from_language',
      translation_to: 'translation_to_language',
      bilingual_mode: 'bilingual_mode_enabled'
    };
    
    this.init();
  }

  init() {
    console.log('[LanguagePrefs] Initializing language preferences system');
    this.loadAllPreferences();
    this.setupLanguageListeners();
  }

  /**
   * Set a cookie with proper options
   */
  setCookie(name, value, options = {}) {
    const opts = { ...this.cookieOptions, ...options };
    let cookieString = `${name}=${encodeURIComponent(value)}`;
    
    if (opts.expires) {
      const date = new Date();
      date.setTime(date.getTime() + (opts.expires * 24 * 60 * 60 * 1000));
      cookieString += `; expires=${date.toUTCString()}`;
    }
    
    if (opts.path) {
      cookieString += `; path=${opts.path}`;
    }
    
    if (opts.sameSite) {
      cookieString += `; SameSite=${opts.sameSite}`;
    }
    
    if (window.location.protocol === 'https:') {
      cookieString += '; Secure';
    }
    
    document.cookie = cookieString;
    console.log(`[LanguagePrefs] Set cookie: ${name}=${value}`);
  }

  /**
   * Get a cookie value
   */
  getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) {
        const value = decodeURIComponent(c.substring(nameEQ.length, c.length));
        console.log(`[LanguagePrefs] Got cookie: ${name}=${value}`);
        return value;
      }
    }
    return null;
  }

  /**
   * Save language preference
   */
  saveLanguagePreference(type, language) {
    const cookieName = this.cookiePrefix + this.preferences[type];
    this.setCookie(cookieName, language);
    
    // Also save to localStorage as fallback
    try {
      localStorage.setItem(cookieName, language);
    } catch (e) {
      console.warn('[LanguagePrefs] LocalStorage not available for fallback');
    }
  }

  /**
   * Load language preference
   */
  loadLanguagePreference(type, defaultValue = 'en') {
    const cookieName = this.cookiePrefix + this.preferences[type];
    let value = this.getCookie(cookieName);
    
    // Fallback to localStorage if cookie not found
    if (!value) {
      try {
        value = localStorage.getItem(cookieName);
      } catch (e) {
        console.warn('[LanguagePrefs] LocalStorage not available for fallback');
      }
    }
    
    return value || defaultValue;
  }

  /**
   * Load all language preferences and apply them
   */
  loadAllPreferences() {
    // Load source language (used for transcription)
    const sourceLanguage = this.loadLanguagePreference('source', 'en');
    this.applyLanguageToDropdowns(['global-language', 'basic-language', 'language-1'], sourceLanguage);
    
    // Load target language (used for translation)
    const targetLanguage = this.loadLanguagePreference('target', 'es');
    this.applyLanguageToDropdowns(['language-2', 'bilingual-to-language'], targetLanguage);
    
    // Load bilingual mode preference
    const bilingualMode = this.loadLanguagePreference('bilingual_mode', 'false') === 'true';
    const bilingualToggle = document.getElementById('bilingual-mode');
    if (bilingualToggle) {
      bilingualToggle.checked = bilingualMode;
      // Trigger change event to update UI
      bilingualToggle.dispatchEvent(new Event('change'));
    }
    
    console.log(`[LanguagePrefs] Loaded preferences - Source: ${sourceLanguage}, Target: ${targetLanguage}, Bilingual: ${bilingualMode}`);
  }

  /**
   * Apply language to multiple dropdowns
   */
  applyLanguageToDropdowns(dropdownIds, language) {
    dropdownIds.forEach(id => {
      const dropdown = document.getElementById(id);
      if (dropdown) {
        dropdown.value = language;
        console.log(`[LanguagePrefs] Applied ${language} to ${id}`);
      }
    });
  }

  /**
   * Setup event listeners for language changes
   */
  setupLanguageListeners() {
    // Source language dropdowns
    const sourceDropdowns = ['global-language', 'basic-language', 'language-1'];
    sourceDropdowns.forEach(id => {
      const dropdown = document.getElementById(id);
      if (dropdown) {
        dropdown.addEventListener('change', (e) => {
          const language = e.target.value;
          this.saveLanguagePreference('source', language);
          
          // Sync with other source language dropdowns
          sourceDropdowns.forEach(otherId => {
            if (otherId !== id) {
              const otherDropdown = document.getElementById(otherId);
              if (otherDropdown) {
                otherDropdown.value = language;
              }
            }
          });
          
          console.log(`[LanguagePrefs] Source language changed to: ${language}`);
        });
      }
    });

    // Target language dropdowns
    const targetDropdowns = ['language-2', 'bilingual-to-language'];
    targetDropdowns.forEach(id => {
      const dropdown = document.getElementById(id);
      if (dropdown) {
        dropdown.addEventListener('change', (e) => {
          const language = e.target.value;
          this.saveLanguagePreference('target', language);
          
          // Sync with other target language dropdowns
          targetDropdowns.forEach(otherId => {
            if (otherId !== id) {
              const otherDropdown = document.getElementById(otherId);
              if (otherDropdown) {
                otherDropdown.value = language;
              }
            }
          });
          
          console.log(`[LanguagePrefs] Target language changed to: ${language}`);
        });
      }
    });

    // Bilingual mode toggle
    const bilingualToggle = document.getElementById('bilingual-mode');
    if (bilingualToggle) {
      bilingualToggle.addEventListener('change', (e) => {
        const isEnabled = e.target.checked;
        this.saveLanguagePreference('bilingual_mode', isEnabled.toString());
        console.log(`[LanguagePrefs] Bilingual mode changed to: ${isEnabled}`);
      });
    }
  }

  /**
   * Get current language preferences
   */
  getCurrentPreferences() {
    return {
      source: this.loadLanguagePreference('source'),
      target: this.loadLanguagePreference('target'),
      bilingualMode: this.loadLanguagePreference('bilingual_mode') === 'true'
    };
  }

  /**
   * Reset all language preferences
   */
  resetPreferences() {
    Object.values(this.preferences).forEach(pref => {
      const cookieName = this.cookiePrefix + pref;
      this.setCookie(cookieName, '', { expires: -1 });
      try {
        localStorage.removeItem(cookieName);
      } catch (e) {
        // Ignore localStorage errors
      }
    });
    
    console.log('[LanguagePrefs] All preferences reset');
    this.loadAllPreferences();
  }
}

// Initialize language preferences when DOM is ready
let languagePreferences;

function initializeLanguagePreferences() {
  if (!languagePreferences) {
    languagePreferences = new LanguagePreferences();
    window.languagePreferences = languagePreferences; // Make globally available
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeLanguagePreferences);
} else {
  initializeLanguagePreferences();
}

console.log('[LanguagePrefs] Language preferences module loaded');
