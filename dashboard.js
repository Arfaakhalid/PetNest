// Dashboard specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if needed
    initializeCharts();
    
    // Activity feed interactions
    const activityItems = document.querySelectorAll('.activity-item');
    activityItems.forEach(item => {
        item.addEventListener('click', function() {
            const activityText = this.querySelector('p').textContent;
            showNotification(`Viewing: ${activityText}`, 'info');
        });
    });
    
    // Quick stats interactions
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(card => {
        card.addEventListener('click', function() {
            const statText = this.querySelector('p').textContent;
            const statValue = this.querySelector('h3').textContent;
            
            showNotification(`${statValue} ${statText}`, 'info');
        });
    });
    
    // Recommended pets "Adopt" buttons
    const dashboardAdoptBtns = document.querySelectorAll('.dashboard-sections .btn-secondary');
    dashboardAdoptBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const petCard = this.closest('.pet-card');
            const petName = petCard.querySelector('h3').textContent;
            
            showAdoptionModal(petName);
        });
    });
    
    // View All Pets link
    const viewAllPetsLink = document.querySelector('.section-footer .btn-link');
    if (viewAllPetsLink) {
        viewAllPatsLink.addEventListener('click', function(e) {
            e.preventDefault();
            showNotification('Redirecting to all pets...', 'info');
            // In real app: window.location.href = 'adopt-pets.html';
        });
    }
});

function initializeCharts() {
    // This would initialize any charts on the dashboard
    // For now, we'll just log that charts would be initialized
    console.log('Initializing dashboard charts...');
    
    // In a real application, you might use Chart.js or similar here
    // Example:
    /*
    const ctx = document.getElementById('adoptionChart').getContext('2d');
    const adoptionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Adoptions',
                data: [12, 19, 3, 5, 2, 3],
                backgroundColor: 'rgba(255, 107, 53, 0.2)',
                borderColor: 'rgba(255, 107, 53, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
    */
}

// Additional dashboard-specific functions can be added here