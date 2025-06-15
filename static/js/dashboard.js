let currentUserRole = 'normal_user';

// Fetch user role immediately when dashboard loads
document.addEventListener('DOMContentLoaded', function() {
    fetchUserRoleInfo();
    
    // Add a slight delay to ensure elements are loaded
    setTimeout(fixSpecificRestrictionMessages, 500);
});

function fetchUserRoleInfo() {
    fetch('/api/user/role-info')
        .then(response => response.json())
        .then(data => {
            console.log('User role data:', data); // Debug log
            currentUserRole = data.role || 'normal_user';
            window.currentUserRole = currentUserRole;
            
            // Check if user is super_user or admin
            if (currentUserRole === 'super_user' || currentUserRole === 'admin') {
                console.log('Unlimited user detected, updating UI');
                applyUnlimitedUserUI();
            }
        })
        .catch(error => {
            console.error('Error fetching user role:', error);
        });
}

function applyUnlimitedUserUI() {
    // Hide all usage restriction indicators
    document.querySelectorAll('.usage-restriction-indicator').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.usage-limit-warning').forEach(el => el.style.display = 'none');
    
    // Replace usage numbers with unlimited indicator
    document.querySelectorAll('.usage-remaining').forEach(el => {
        el.textContent = 'Unlimited';
    });
    
    // Hide any "not available on Free Plan" messages
    document.querySelectorAll('.feature-not-available').forEach(el => {
        el.style.display = 'none';
    });
    
    // Remove translation restriction banners
    document.querySelectorAll('.translation-not-available').forEach(el => {
        el.style.display = 'none';
    });
    
    // Remove TTS restriction banners
    document.querySelectorAll('.tts-not-available').forEach(el => {
        el.style.display = 'none';
    });
}

function updateDashboardUI(userData) {
    // Get user role - first try from userData, then from window object
    const userRole = userData.role || window.currentUserRole || 'normal_user';
    const isUnlimitedUser = (userRole === 'admin' || userRole === 'super_user');
    
    console.log('Updating dashboard UI with role:', userRole); // Debug log
    
    // Store role in window object for other components
    window.currentUserRole = userRole;
    
    // Update usage displays
    if (isUnlimitedUser) {
        applyUnlimitedUserUI();
    } else {
        // Normal users see regular usage limits
        // Existing code for normal users...
    }
}

// Add this function to directly target the specific elements in your screenshot
function fixSpecificRestrictionMessages() {
    // Get user role
    const userRole = window.currentUserRole || 'normal_user';
    const isUnlimitedUser = (userRole === 'admin' || userRole === 'super_user');
    
    if (isUnlimitedUser) {
        // Target the specific translation not available message
        const translationNotAvailable = document.querySelector('[data-testid="translation-not-available"]');
        if (translationNotAvailable) {
            translationNotAvailable.style.display = 'none';
        }
        
        // Target all elements containing "Translation not available on Free Plan"
        document.querySelectorAll('*').forEach(el => {
            if (el.textContent && el.textContent.includes('Translation not available on Free Plan')) {
                el.style.display = 'none';
            }
        });
        
        // Target all elements containing "TTS not available on Free Plan"
        document.querySelectorAll('*').forEach(el => {
            if (el.textContent && el.textContent.includes('TTS not available on Free Plan')) {
                el.style.display = 'none';
            }
        });
    }
}

// Also add a mutation observer to catch dynamically added elements
const observer = new MutationObserver(function(mutations) {
    fixSpecificRestrictionMessages();
});

// Start observing the document with the configured parameters
observer.observe(document.body, { childList: true, subtree: true });

