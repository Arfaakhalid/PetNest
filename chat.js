// Chat functionality
document.addEventListener('DOMContentLoaded', function() {
    // Chat item selection
    const chatItems = document.querySelectorAll('.chat-item');
    chatItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            chatItems.forEach(i => i.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
            
            // In a real app, this would load the conversation
            const userName = this.querySelector('h4').textContent;
            showNotification(`Loading conversation with ${userName}`, 'info');
        });
    });
    
    // Send message functionality
    const chatInput = document.querySelector('.chat-input input');
    const sendBtn = document.querySelector('.send-btn');
    
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // File attachment simulation
    const attachBtn = document.querySelector('.fa-paperclip').closest('.btn-icon');
    if (attachBtn) {
        attachBtn.addEventListener('click', function() {
            showNotification('File attachment feature would open here', 'info');
        });
    }
    
    // Image attachment simulation
    const imageBtn = document.querySelector('.fa-image').closest('.btn-icon');
    if (imageBtn) {
        imageBtn.addEventListener('click', function() {
            showNotification('Image picker would open here', 'info');
        });
    }
    
    // Emoji picker simulation
    const emojiBtn = document.querySelector('.fa-smile').closest('.btn-icon');
    if (emojiBtn) {
        emojiBtn.addEventListener('click', function() {
            showNotification('Emoji picker would open here', 'info');
        });
    }
    
    // Download attachment
    const downloadBtns = document.querySelectorAll('.download-btn');
    downloadBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            showNotification('File download started', 'success');
        });
    });
    
    // Simulate receiving messages (for demo purposes)
    simulateIncomingMessages();
});

function sendMessage() {
    const chatInput = document.querySelector('.chat-input input');
    const message = chatInput.value.trim();
    
    if (message === '') return;
    
    const chatMessages = document.querySelector('.chat-messages');
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.className = 'message sent';
    messageElement.innerHTML = `
        <div class="message-content">
            <p>${message}</p>
            <span class="message-time">${getCurrentTime()}</span>
        </div>
    `;
    
    // Add to chat
    chatMessages.appendChild(messageElement);
    
    // Clear input
    chatInput.value = '';
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Simulate reply after a delay
    setTimeout(simulateReply, 1000 + Math.random() * 2000);
}

function simulateReply() {
    const replies = [
        "Thanks for your message!",
        "I'll get back to you shortly.",
        "That's a great question! Let me check.",
        "I'm available to meet this weekend.",
        "The pet is still available for adoption."
    ];
    
    const randomReply = replies[Math.floor(Math.random() * replies.length)];
    const chatMessages = document.querySelector('.chat-messages');
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message received';
    messageElement.innerHTML = `
        <div class="message-avatar">
            <img src="../../assets/images/users/user2.jpg" alt="User">
        </div>
        <div class="message-content">
            <p>${randomReply}</p>
            <span class="message-time">${getCurrentTime()}</span>
        </div>
    `;
    
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function simulateIncomingMessages() {
    // Simulate occasional incoming messages when not actively chatting
    setInterval(() => {
        // Only simulate if user hasn't sent a message recently
        const lastMessage = document.querySelector('.message.sent:last-child');
        if (!lastMessage) return;
        
        const lastMessageTime = new Date();
        const now = new Date();
        const diffMinutes = (now - lastMessageTime) / (1000 * 60);
        
        // If no message sent in the last 2 minutes, simulate a message
        if (diffMinutes > 2 && Math.random() < 0.3) {
            const prompts = [
                "Hi! Are you still interested in adopting?",
                "I wanted to follow up about our conversation.",
                "The pet is still available if you're interested!",
                "Let me know if you have any other questions."
            ];
            
            const randomPrompt = prompts[Math.floor(Math.random() * prompts.length)];
            const chatMessages = document.querySelector('.chat-messages');
            
            const messageElement = document.createElement('div');
            messageElement.className = 'message received';
            messageElement.innerHTML = `
                <div class="message-avatar">
                    <img src="../../assets/images/users/user2.jpg" alt="User">
                </div>
                <div class="message-content">
                    <p>${randomPrompt}</p>
                    <span class="message-time">${getCurrentTime()}</span>
                </div>
            `;
            
            chatMessages.appendChild(messageElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Update notification badge
            const activeChat = document.querySelector('.chat-item.active');
            if (activeChat) {
                let badge = activeChat.querySelector('.chat-badge');
                if (!badge) {
                    badge = document.createElement('div');
                    badge.className = 'chat-badge';
                    activeChat.appendChild(badge);
                }
                const currentCount = parseInt(badge.textContent) || 0;
                badge.textContent = currentCount + 1;
            }
        }
    }, 30000); // Check every 30 seconds
}

function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}


// assets/js/chat.js

function initChat() {
    // Conversation switching
    const conversations = document.querySelectorAll('.conversation');
    const chatArea = document.querySelector('.chat-area');
    
    conversations.forEach(convo => {
        convo.addEventListener('click', function() {
            // Remove active class from all conversations
            conversations.forEach(c => c.classList.remove('active'));
            // Add active class to clicked conversation
            this.classList.add('active');
            
            // In a real app, this would load the conversation from server
            const chatId = this.getAttribute('data-chat');
            loadConversation(chatId);
        });
    });
    
    // Send message functionality
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            // Create new message element
            const messageElement = document.createElement('div');
            messageElement.className = 'message sent';
            messageElement.innerHTML = `
                <div class="message-content">
                    <p>${message}</p>
                    <span class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
            `;
            
            // Add to chat
            document.querySelector('.chat-messages').appendChild(messageElement);
            
            // Clear input
            messageInput.value = '';
            
            // Scroll to bottom
            const chatMessages = document.querySelector('.chat-messages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // In a real app, send message to server here
        }
    }
    
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // View profile functionality
    const profileButtons = document.querySelectorAll('.btn-icon[title="View Profile"]');
    const profileSidebar = document.querySelector('.user-profile-sidebar');
    const closeProfile = document.querySelector('.close-profile');
    
    profileButtons.forEach(button => {
        button.addEventListener('click', function() {
            profileSidebar.style.display = 'block';
        });
    });
    
    if (closeProfile) {
        closeProfile.addEventListener('click', function() {
            profileSidebar.style.display = 'none';
        });
    }
    
    // Close deal functionality
    const closeDealButtons = document.querySelectorAll('.btn-icon[title="Close Deal"]');
    
    closeDealButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (confirm('Mark this conversation as a completed deal? This will archive the conversation.')) {
                // In a real app, this would update the deal status on the server
                showNotification('Deal marked as completed successfully!', 'success');
            }
        });
    });
}

function loadConversation(chatId) {
    // In a real app, this would fetch conversation data from the server
    // For now, we'll just simulate loading
    const chatMessages = document.querySelector('.chat-messages');
    chatMessages.innerHTML = `
        <div class="message received">
            <div class="message-content">
                <p>Loading conversation...</p>
            </div>
        </div>
    `;
    
    // Simulate API call delay
    setTimeout(() => {
        // This would be the actual conversation data from the server
        chatMessages.innerHTML = `
            <div class="message received">
                <div class="message-content">
                    <p>Hello! I'm interested in your pet listing.</p>
                    <span class="message-time">10:30 AM</span>
                </div>
            </div>
            <div class="message sent">
                <div class="message-content">
                    <p>Thanks for your interest! What would you like to know?</p>
                    <span class="message-time">10:32 AM</span>
                </div>
            </div>
        `;
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 500);
}