// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const fileInput = document.getElementById('fileInput');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

function initializeEventListeners() {
    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    // Send message on Enter (but allow Shift+Enter for new lines)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // File upload handling
    fileInput.addEventListener('change', handleFileUpload);
}

function handleFileUpload(e) {
    const files = Array.from(e.target.files);
    files.forEach(file => {
        if (file.type.startsWith('image/')) {
            displayImageMessage(file);
        } else {
            displayFileMessage(file);
        }
    });
    // Clear the input
    e.target.value = '';
}

function displayImageMessage(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        appendMessage(`
            <div style="display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-image" style="color: #667eea;"></i>
                <span>${file.name}</span>
            </div>
            <img src="${e.target.result}" class="message-image" alt="Uploaded image">
        `, 'user', true);
    };
    reader.readAsDataURL(file);
}

function displayFileMessage(file) {
    const fileSize = (file.size / 1024).toFixed(1);
    appendMessage(`
        <div style="display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-file" style="color: #667eea;"></i>
            <span>${file.name}</span>
            <span style="font-size: 0.8rem; opacity: 0.7;">(${fileSize} KB)</span>
        </div>
    `, 'user', true);
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Disable input and button
    messageInput.disabled = true;
    sendButton.disabled = true;

    // Add user message
    appendMessage(message, 'user');

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Add typing indicator
    appendTypingIndicator();

    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: message })
        });

        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add bot response
        appendMessage(data.response || 'Sorry, I couldn\'t process your request.', 'bot');
        
        // Check if response contains location data and update map
        if (data.response) {
            handleMapIntegration(data.response, message);
        }
        
    } catch (error) {
        removeTypingIndicator();
        appendMessage('Sorry, there was an error processing your request. Please try again.', 'bot');
        console.error('Error:', error);
    }

    // Re-enable input and button
    messageInput.disabled = false;
    sendButton.disabled = false;
    messageInput.focus();
}

function handleMapIntegration(response, userMessage) {
    // Check if the user is asking about a specific location
    const locationKeywords = ['fire', 'wildfire', 'burning', 'location', 'where', 'show me'];
    const hasLocationKeywords = locationKeywords.some(keyword => 
        userMessage.toLowerCase().includes(keyword)
    );
    
    if (hasLocationKeywords && window.mapManager) {
        // Try to extract location from user message
        const locationMatch = extractLocationFromText(userMessage);
        if (locationMatch) {
            // Add a small delay to let the message appear first
            setTimeout(() => {
                mapManager.searchAndAddLocation(locationMatch, {
                    severity: 'medium',
                    description: `Fire incident mentioned at ${locationMatch}`
                });
            }, 1000);
        }
        
        // Also try to parse the LLM response for location data
        setTimeout(() => {
            window.handleLLMLocationResponse(response);
        }, 1500);
    }
}

function extractLocationFromText(text) {
    // Common location patterns
    const patterns = [
        /(?:in|at|near|around)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/g,
        /(?:fire|wildfire)\s+(?:in|at|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/g,
        /([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:fire|wildfire)/g
    ];
    
    for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match && match[1]) {
            return match[1].trim();
        }
    }
    
    // If no pattern matches, try to find capitalized words that might be locations
    const words = text.split(' ');
    const potentialLocations = words.filter(word => 
        word.length > 2 && 
        word[0] === word[0].toUpperCase() && 
        !['The', 'This', 'That', 'These', 'Those', 'What', 'Where', 'When', 'Why', 'How'].includes(word)
    );
    
    return potentialLocations.length > 0 ? potentialLocations[0] : null;
}

function appendMessage(content, sender, isHTML = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (isHTML) {
        contentDiv.innerHTML = content;
    } else {
        contentDiv.textContent = content;
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot';
    typingDiv.id = 'typing-indicator';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'typing-indicator';
    typingContent.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    
    typingDiv.appendChild(avatar);
    typingDiv.appendChild(typingContent);
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Export functions for global access
window.sendMessage = sendMessage; 