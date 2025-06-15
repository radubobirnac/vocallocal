function updateModelAccessUI() {
    // Get user role from window object
    const userRole = window.currentUserRole || 'normal_user';
    const isUnlimitedUser = (userRole === 'admin' || userRole === 'super_user');
    
    // Update model dropdowns
    document.querySelectorAll('.model-dropdown').forEach(dropdown => {
        if (isUnlimitedUser) {
            // Remove lock icons from all options
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