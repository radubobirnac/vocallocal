/**
 * Super User Fix - Directly targets elements in the dashboard
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is super_user or admin
    fetch('/api/user/role-info')
        .then(response => response.json())
        .then(data => {
            console.log('User role data:', data);
            const isUnlimitedUser = (data.role === 'super_user' || data.role === 'admin');
            
            if (isUnlimitedUser) {
                console.log('Super user detected, applying direct fixes');
                
                // Change the plan display at the top from "Free Plan" to "Professional Plan"
                const planElements = document.querySelectorAll('.plan-badge, .plan-display, .plan-indicator');
                planElements.forEach(el => {
                    if (el.textContent.includes('Free Plan')) {
                        el.textContent = 'Professional Plan';
                        el.style.backgroundColor = '#4CAF50';
                    }
                });
                
                // If no specific plan element found, try to find by text content
                document.querySelectorAll('*').forEach(el => {
                    if (el.textContent === 'Free Plan' && el.children.length === 0) {
                        el.textContent = 'Professional Plan';
                        el.style.backgroundColor = '#4CAF50';
                    }
                });
                
                // Remove all restriction messages
                const restrictionMessages = [
                    'Translation not available on Free Plan',
                    'TTS not available on Free Plan',
                    'AI credits not available on Free Plan'
                ];
                
                // Target the specific alert elements
                document.querySelectorAll('.alert, .alert-danger, [class*="alert"]').forEach(el => {
                    restrictionMessages.forEach(message => {
                        if (el.textContent.includes(message)) {
                            console.log('Removing restriction message:', el.textContent.trim());
                            el.remove();
                        }
                    });
                });
                
                // Replace all usage displays with "Unlimited"
                document.querySelectorAll('.remaining, [class*="remaining"]').forEach(el => {
                    el.textContent = 'Unlimited';
                });
                
                // Remove all progress bars
                document.querySelectorAll('.progress, [class*="progress"]').forEach(el => {
                    const parent = el.parentElement;
                    if (parent) {
                        const unlimitedIndicator = document.createElement('div');
                        unlimitedIndicator.className = 'unlimited-indicator';
                        unlimitedIndicator.textContent = 'Unlimited';
                        unlimitedIndicator.style.color = '#4CAF50';
                        unlimitedIndicator.style.fontWeight = 'bold';
                        parent.replaceChild(unlimitedIndicator, el);
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error fetching user role:', error);
        });
});