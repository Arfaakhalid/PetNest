document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle
    const themeToggle = document.querySelector('.theme-toggle');
    const body = document.body;

    themeToggle.addEventListener('click', () => {
        if (body.getAttribute('data-theme') === 'dark') {
            body.removeAttribute('data-theme');
            localStorage.removeItem('theme');
        } else {
            body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        }
    });

    // Load saved theme
    if (localStorage.getItem('theme') === 'dark') {
        body.setAttribute('data-theme', 'dark');
    }

    // Scroll Animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.fade-in-up, .slide-in-left, .slide-in-right, .slide-in-up').forEach(element => {
        observer.observe(element);
    });

    // Particle Animation
    const particleContainer = document.querySelector('.particle-container');
    for (let i = 0; i < 3; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        particle.style.width = `${20 + i * 10}px`;
        particle.style.height = `${20 + i * 10}px`;
        particleContainer.appendChild(particle);
    }

    // Date and Time
    function updateDateTime() {
        const now = new Date();
        const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const timeOptions = { hour: '2-digit', minute: '2-digit', hour12: true, timeZone: 'Asia/Karachi' };
        const date = now.toLocaleDateString('en-US', dateOptions);
        const time = now.toLocaleTimeString('en-US', timeOptions);
        document.getElementById('current-date').textContent = date;
        document.getElementById('current-time').textContent = time;
    }
    updateDateTime();
    setInterval(updateDateTime, 1000);
});


// Theme Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle
    const themeToggle = document.getElementById('darkModeToggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    if (currentTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        themeToggle.checked = true;
    }
    
    themeToggle.addEventListener('change', function() {
        if (this.checked) {
            document.body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }
    });
    
    // Sidebar toggle for mobile
    const toggleSidebar = document.getElementById('toggleSidebar');
    const sidebar = document.getElementById('sidebar');
    
    if (toggleSidebar && sidebar) {
        toggleSidebar.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
    
    // Tab functionality
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Remove active class from all tabs and contents
            document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Add active class to current tab and content
            this.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
    
    // Favorite buttons
    const favoriteBtns = document.querySelectorAll('.favorite-btn');
    favoriteBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            this.classList.toggle('active');
            this.querySelector('i').classList.toggle('far');
            this.querySelector('i').classList.toggle('fas');
            
            // Show notification
            showNotification('Pet added to favorites!', 'success');
        });
    });
    
    // Remove favorite functionality
    const removeFavoriteBtns = document.querySelectorAll('.remove-favorite');
    removeFavoriteBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const favoriteItem = this.closest('.favorite-item');
            favoriteItem.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                favoriteItem.remove();
                
                // Check if favorites are empty
                const favoritesGrid = document.querySelector('.favorites-grid');
                if (!favoritesGrid || favoritesGrid.children.length === 0) {
                    document.getElementById('emptyFavorites').style.display = 'block';
                }
                
                showNotification('Pet removed from favorites', 'info');
            }, 300);
        });
    });
    
    // Form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            showNotification('Settings saved successfully!', 'success');
        });
    });
    
    // Price range display
    const priceRange = document.getElementById('maxPrice');
    if (priceRange) {
        const priceValue = document.querySelector('.price-value');
        priceRange.addEventListener('input', function() {
            const value = parseInt(this.value).toLocaleString();
            priceValue.textContent = `Rs ${value}`;
        });
    }
});

// Notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close"><i class="fas fa-times"></i></button>
    `;
    
    // Add styles for notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        max-width: 350px;
    `;
    
    if (type === 'success') {
        notification.style.borderLeft = '4px solid #48BB78';
    } else if (type === 'error') {
        notification.style.borderLeft = '4px solid #F56565';
    } else {
        notification.style.borderLeft = '4px solid #4299E1';
    }
    
    document.body.appendChild(notification);
    
    // Close button
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    });
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    @keyframes fadeOut {
        from { opacity: 1; transform: scale(1); }
        to { opacity: 0; transform: scale(0.8); }
    }
    
    .notification-close {
        background: none;
        border: none;
        color: #718096;
        cursor: pointer;
        padding: 5px;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    
    .notification-close:hover {
        background: #F7FAFC;
        color: #2D3748;
    }
`;
document.head.appendChild(style);

// assets/js/main.js

// Theme Toggle Functionality
function initTheme() {
    const themeToggle = document.getElementById('theme-toggle-btn');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    if (themeToggle) {
        // Update button icon based on current theme
        updateThemeIcon(currentTheme);
        
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            updateThemeIcon(newTheme);
        });
    }
}

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('theme-toggle-btn');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
        } else {
            icon.className = 'fas fa-moon';
        }
    }
}

// Component Loading
function loadComponent(elementId, filePath) {
    fetch(filePath)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(data => {
            document.getElementById(elementId).innerHTML = data;
            
            // Re-initialize theme toggle if it's in the loaded component
            if (elementId === 'header') {
                initTheme();
            }
        })
        .catch(error => {
            console.error('Error loading component:', error);
            document.getElementById(elementId).innerHTML = '<p>Error loading component</p>';
        });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    
    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Form validation helper
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.style.borderColor = 'var(--error-color)';
        } else {
            input.style.borderColor = '';
        }
    });
    
    return isValid;
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="notification-close">&times;</button>
    `;
    
    // Add styles if not already added
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                color: white;
                z-index: 1000;
                display: flex;
                align-items: center;
                gap: 1rem;
                max-width: 400px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                animation: slideIn 0.3s ease;
            }
            .notification-info { background: var(--primary-color); }
            .notification-success { background: var(--success-color); }
            .notification-error { background: var(--error-color); }
            .notification-warning { background: var(--warning-color); }
            .notification-close {
                background: none;
                border: none;
                color: white;
                font-size: 1.2rem;
                cursor: pointer;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
    
    // Close on click
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.remove();
    });
}