// adopt page helpers (kept minimal; main logic inline in adopt.html)
// Adopt page specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Filter functionality
    const filters = {
        animalType: document.getElementById('animalType'),
        location: document.getElementById('location'),
        breed: document.getElementById('breed'),
        sortBy: document.getElementById('sortBy')
    };
    
    // Apply filters when any filter changes
    Object.values(filters).forEach(filter => {
        if (filter) {
            filter.addEventListener('change', applyFilters);
        }
    });
    
    // Search functionality
    const searchBox = document.querySelector('.search-box input');
    const searchBtn = document.querySelector('.search-box .btn-primary');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', performSearch);
    }
    
    if (searchBox) {
        searchBox.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
    
    // Adopt button functionality
    const adoptBtns = document.querySelectorAll('.btn-secondary');
    adoptBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const petCard = this.closest('.pet-card');
            const petName = petCard.querySelector('h3').textContent;
            
            showAdoptionModal(petName);
        });
    });
    
    // View details button
    const viewDetailsBtns = document.querySelectorAll('.btn-primary');
    viewDetailsBtns.forEach(btn => {
        if (btn.textContent.includes('View Details')) {
            btn.addEventListener('click', function() {
                const petCard = this.closest('.pet-card');
                const petName = petCard.querySelector('h3').textContent;
                const petBreed = petCard.querySelector('.pet-breed').textContent;
                
                // In a real app, this would redirect to a pet details page
                showNotification(`Viewing details for ${petName} (${petBreed})`, 'info');
            });
        }
    });
});

function applyFilters() {
    const filters = {
        animalType: document.getElementById('animalType').value,
        location: document.getElementById('location').value,
        breed: document.getElementById('breed').value,
        sortBy: document.getElementById('sortBy').value
    };
    
    // Show loading state
    const petsGrid = document.querySelector('.pets-grid');
    petsGrid.style.opacity = '0.5';
    
    // Simulate API call delay
    setTimeout(() => {
        // In a real app, this would make an API call with the filters
        console.log('Applying filters:', filters);
        
        // Remove loading state
        petsGrid.style.opacity = '1';
        
        showNotification('Filters applied successfully', 'success');
    }, 500);
}

function performSearch() {
    const searchTerm = document.querySelector('.search-box input').value;
    
    if (searchTerm.trim() === '') {
        showNotification('Please enter a search term', 'error');
        return;
    }
    
    // Show loading state
    const petsGrid = document.querySelector('.pets-grid');
    petsGrid.style.opacity = '0.5';
    
    // Simulate API call delay
    setTimeout(() => {
        // In a real app, this would make an API call with the search term
        console.log('Searching for:', searchTerm);
        
        // Remove loading state
        petsGrid.style.opacity = '1';
        
        showNotification(`Found results for "${searchTerm}"`, 'success');
    }, 800);
}

function showAdoptionModal(petName) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Adopt ${petName}</h3>
                <button class="modal-close"><i class="fas fa-times"></i></button>
            </div>
            <div class="modal-body">
                <p>You're about to start the adoption process for <strong>${petName}</strong>.</p>
                <p>This will:</p>
                <ul>
                    <li>Connect you with the pet's owner</li>
                    <li>Open a chat for communication</li>
                    <li>Begin the adoption paperwork process</li>
                </ul>
                <div class="modal-actions">
                    <button class="btn-outline" id="cancelAdoption">Cancel</button>
                    <button class="btn-primary" id="confirmAdoption">Start Adoption Process</button>
                </div>
            </div>
        </div>
    `;
    
    // Add styles
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.3s ease;
    `;
    
    const modalContent = modal.querySelector('.modal-content');
    modalContent.style.cssText = `
        background: white;
        padding: 0;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        max-width: 500px;
        width: 90%;
        animation: scaleIn 0.3s ease;
    `;
    
    document.body.appendChild(modal);
    
    // Close modal functionality
    const closeBtn = modal.querySelector('.modal-close');
    const cancelBtn = modal.querySelector('#cancelAdoption');
    
    function closeModal() {
        modal.style.animation = 'fadeOut 0.3s ease';
        modalContent.style.animation = 'scaleOut 0.3s ease';
        setTimeout(() => modal.remove(), 300);
    }
    
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    
    // Confirm adoption
    const confirmBtn = modal.querySelector('#confirmAdoption');
    confirmBtn.addEventListener('click', function() {
        // In a real app, this would initiate the adoption process
        showNotification(`Adoption process started for ${petName}!`, 'success');
        closeModal();
        
        // Redirect to chat page in a real application
        setTimeout(() => {
            // window.location.href = 'chat.html';
            showNotification(`You can now chat with ${petName}'s owner`, 'info');
        }, 1000);
    });
    
    // Add CSS animations for modal
    if (!document.querySelector('#modal-animations')) {
        const style = document.createElement('style');
        style.id = 'modal-animations';
        style.textContent = `
            @keyframes scaleIn {
                from { transform: scale(0.8); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
            
            @keyframes scaleOut {
                from { transform: scale(1); opacity: 1; }
                to { transform: scale(0.8); opacity: 0; }
            }
            
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            
            .modal-header {
                padding: 20px 25px;
                border-bottom: 1px solid #E2E8F0;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .modal-header h3 {
                margin: 0;
                font-size: 20px;
            }
            
            .modal-close {
                background: none;
                border: none;
                font-size: 18px;
                color: #718096;
                cursor: pointer;
                padding: 5px;
                border-radius: 4px;
            }
            
            .modal-close:hover {
                background: #F7FAFC;
                color: #2D3748;
            }
            
            .modal-body {
                padding: 25px;
            }
            
            .modal-body ul {
                margin: 15px 0;
                padding-left: 20px;
            }
            
            .modal-body li {
                margin-bottom: 8px;
            }
            
            .modal-actions {
                display: flex;
                gap: 10px;
                justify-content: flex-end;
                margin-top: 25px;
            }
        `;
        document.head.appendChild(style);
    }
}