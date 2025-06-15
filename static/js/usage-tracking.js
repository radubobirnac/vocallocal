async function trackUsage(serviceType, amount) {
    // Always track usage for all users (including super users) for analytics
    try {
        const response = await fetch('/api/track-usage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                service_type: serviceType,
                amount: amount
            })
        });
        
        if (!response.ok) {
            console.error(`Error tracking usage: ${response.status}`);
        }
    } catch (error) {
        console.error('Error tracking usage:', error);
    }
}