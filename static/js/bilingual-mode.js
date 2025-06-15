async function initBilingualMode() {
    // Check user role
    const userRole = window.currentUserRole || 'normal_user';
    const isUnlimitedUser = (userRole === 'admin' || userRole === 'super_user');
    
    // Get translation model dropdown
    const translationModelSelect = document.getElementById('translation-model-select');
    
    // For super users, remove any lock icons from model options
    if (isUnlimitedUser && translationModelSelect) {
        Array.from(translationModelSelect.options).forEach(option => {
            option.text = option.text.replace(' 🔒', '');
        });
    }
    
    // Remove translation restrictions for super users
    const translationRestrictionBanner = document.querySelector('.translation-restriction-banner');
    if (isUnlimitedUser && translationRestrictionBanner) {
        translationRestrictionBanner.style.display = 'none';
    }
}

// Modify the translation function to bypass UI restrictions for super users
async function translateText(text, targetLang) {
    const userRole = window.currentUserRole || 'normal_user';
    const isUnlimitedUser = (userRole === 'admin' || userRole === 'super_user');
    
    // For tracking purposes, still count words but don't enforce limits for super users
    const wordCount = text.split(' ').length;
    
    // Only check usage for normal users
    if (!isUnlimitedUser) {
        // Existing usage check code...
    }
    
    // Continue with translation for all users
    // Existing translation code...
    
    // Track usage for analytics (for all users including super users)
    try {
        trackUsage('translation', wordCount);
    } catch (error) {
        console.error('Error tracking translation usage:', error);
    }
}