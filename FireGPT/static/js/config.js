// Application Configuration
const CONFIG = {
    // API Endpoints
    API_ENDPOINTS: {
        ASK: '/ask',
        UPLOAD: '/upload'
    },
    
    // UI Settings
    UI: {
        MAX_MESSAGE_LENGTH: 1000,
        TYPING_INDICATOR_DELAY: 1000,
        AUTO_SCROLL_DELAY: 100,
        MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
        SUPPORTED_FILE_TYPES: [
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
    },
    
    // Chat Settings
    CHAT: {
        MAX_MESSAGES_IN_MEMORY: 100,
        MESSAGE_FADE_DURATION: 300,
        TYPING_ANIMATION_DURATION: 1400
    },
    
    // Map Settings
    MAP: {
        DEFAULT_ZOOM: 3,
        DEFAULT_CENTER: { lat: 20, lng: 0 },
        UPDATE_INTERVAL: 30000 // 30 seconds
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else {
    window.CONFIG = CONFIG;
} 