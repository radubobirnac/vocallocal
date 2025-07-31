function updateModelAccessUI() {
    // Get user role and plan from window object
    const userRole = window.currentUserRole || 'normal_user';
    const userPlan = window.currentUserPlan || 'free';
    const isUnlimitedUser = (userRole === 'admin' || userRole === 'super_user');
    const hasBasicOrHigher = (userPlan === 'basic' || userPlan === 'professional');

    // Update model dropdowns
    document.querySelectorAll('.model-dropdown').forEach(dropdown => {
        if (isUnlimitedUser || hasBasicOrHigher) {
            // Remove lock icons from all options for admin/super users and Basic+ plan users
            Array.from(dropdown.options).forEach(option => {
                option.text = option.text.replace(' 🔒', '');
                option.disabled = false;
            });

            // Remove any "premium only" indicators
            const premiumIndicators = document.querySelectorAll('.premium-model-indicator');
            premiumIndicators.forEach(indicator => {
                indicator.style.display = 'none';
            });
        }
    });
    
    // Update any "upgrade required" messages
    if (isUnlimitedUser) {
        document.querySelectorAll('.upgrade-required-message').forEach(msg => {
            msg.style.display = 'none';
        });
    }
}

// Call this function when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Fetch user role info first
    fetch('/api/user/role-info')
        .then(response => response.json())
        .then(data => {
            window.currentUserRole = data.role || 'normal_user';
            updateModelAccessUI();
        })
        .catch(error => {
            console.error('Error fetching user role:', error);
        });
});