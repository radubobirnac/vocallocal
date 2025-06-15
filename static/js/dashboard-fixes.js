/**
 * Dashboard fixes for Super User role
 * This script specifically targets the elements shown in the screenshot
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is super_user or admin
    fetch('/api/user/role-info')
        .then(response => response.json())
        .then(data => {
            console.log('User role data:', data);
            const isUnlimitedUser = (data.role === 'super_user' || data.role === 'admin');
            
            if (isUnlimitedUser) {
                console.log('Super user detected, applying fixes');
                
                // Fix for translation not available message - use multiple selectors
                const translationNotAvailable = document.querySelector('.translation-not-available');
                if (translationNotAvailable) {
                    translationNotAvailable.remove();
                }
                
                // Target all possible translation restriction messages with multiple selectors
                document.querySelectorAll('.alert-danger, .limit-reached, [data-testid="translation-not-available"], [class*="translation-"], [class*="not-available"]').forEach(el => {
                    if (el.textContent && (
                        el.textContent.includes('Translation not available') || 
                        el.textContent.includes('TTS not available') ||
                        el.textContent.includes('not available on') ||
                        el.textContent.includes('limit reached')
                    )) {
                        console.log('Removing restriction message:', el.textContent.trim());
                        el.remove(); // Remove completely instead of just hiding
                    }
                });
                
                // Target the specific elements from the screenshot
                document.querySelectorAll('[class*="alert-"], [class*="danger"]').forEach(el => {
                    if (el.textContent && (
                        el.textContent.includes('Translation not available on Free Plan') ||
                        el.textContent.includes('TTS not available on Free Plan')
                    )) {
                        console.log('Removing plan restriction message:', el.textContent.trim());
                        el.remove();
                    }
                });
                
                // Remove lock symbols from all elements
                document.querySelectorAll('*').forEach(el => {
                    if (el.textContent && el.textContent.includes('🔒')) {
                        el.textContent = el.textContent.replace('🔒', '');
                    }
                });
                
                // Replace usage numbers with unlimited
                document.querySelectorAll('.usage-remaining, [data-testid="remaining-indicator"], .remaining').forEach(el => {
                    el.textContent = 'Unlimited';
                });
                
                // Remove any progress bars showing limits
                document.querySelectorAll('.progress, .progress-bar, [class*="progress"]').forEach(el => {
                    const parent = el.parentElement;
                    if (parent) {
                        const unlimitedIndicator = document.createElement('div');
                        unlimitedIndicator.className = 'unlimited-indicator';
                        unlimitedIndicator.textContent = 'Unlimited access';
                        unlimitedIndicator.style.color = '#4CAF50';
                        unlimitedIndicator.style.fontWeight = 'bold';
                        parent.replaceChild(unlimitedIndicator, el);
                    }
                });
                
                // Add a more aggressive approach for the specific elements in the screenshot
                setTimeout(() => {
                    // Target elements by their text content
                    document.querySelectorAll('*').forEach(el => {
                        if (el.childNodes && el.childNodes.length > 0) {
                            for (let i = 0; i < el.childNodes.length; i++) {
                                const node = el.childNodes[i];
                                if (node.nodeType === Node.TEXT_NODE) {
                                    const text = node.textContent;
                                    if (text && (
                                        text.includes('Translation not available') ||
                                        text.includes('TTS not available')
                                    )) {
                                        console.log('Found restriction text, removing parent element');
                                        if (el.parentElement) {
                                            el.parentElement.remove();
                                        } else {
                                            el.remove();
                                        }
                                        break;
                                    }
                                }
                            }
                        }
                    });
                }, 500); // Slight delay to ensure DOM is fully loaded
            }
        })
        .catch(error => {
            console.error('Error fetching user role:', error);
        });
});

