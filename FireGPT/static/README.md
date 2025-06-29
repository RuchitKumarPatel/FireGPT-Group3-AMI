# FireGPT Static Assets

This directory contains all the static assets for the FireGPT web application, organized in a production-ready structure.

## 📁 Directory Structure

```
static/
├── css/
│   ├── styles.css          # Main application styles
│   └── components.css      # Reusable component styles
├── js/
│   ├── config.js           # Application configuration
│   ├── utils.js            # Utility functions
│   └── app.js              # Main application logic
├── index.html              # Main HTML file
├── index_simple.html       # Simple version (legacy)
└── README.md               # This file
```

## 🎨 CSS Files

### `css/styles.css`
Contains the main application styles including:
- Layout and grid system
- Chat interface styling
- Map section styling
- Responsive design
- Animations and transitions

### `css/components.css`
Contains reusable component styles including:
- Notifications
- Modals
- Buttons
- Cards
- Badges
- Tooltips
- Loading spinners

## 🔧 JavaScript Files

### `js/config.js`
Application configuration and constants:
- API endpoints
- UI settings
- File upload limits
- Chat settings
- Map configuration

### `js/utils.js`
Utility functions for common operations:
- File validation and formatting
- DOM manipulation helpers
- Notification system
- Debouncing functions
- HTML sanitization

### `js/app.js`
Main application logic:
- Chat functionality
- File upload handling
- Message display
- API communication
- Event listeners

## 🚀 Production Benefits

### Performance
- **Separated concerns**: CSS and JS are split for better caching
- **Modular structure**: Easy to maintain and update individual components
- **Optimized loading**: Files are loaded in the correct order

### Maintainability
- **Clear organization**: Each file has a specific purpose
- **Reusable components**: CSS classes and JS functions can be reused
- **Configuration-driven**: Easy to modify settings without touching core logic

### Scalability
- **Component-based**: Easy to add new features
- **Modular architecture**: Can easily extend functionality
- **Production-ready**: Follows web development best practices

## 📱 Features

### Chat Interface
- Modern, responsive design
- Real-time typing indicators
- File upload support
- Message history
- Auto-scrolling

### File Upload
- Drag & drop support
- Multiple file selection
- File type validation
- Size limits
- Progress indicators

### Map Integration
- Placeholder for world map
- Ready for real-time data
- Responsive layout

### Notifications
- Toast notifications
- Multiple types (success, error, warning, info)
- Auto-dismiss
- Smooth animations

## 🔧 Development

### Adding New Features
1. Add styles to appropriate CSS file
2. Add utility functions to `utils.js` if needed
3. Add configuration to `config.js` if required
4. Implement logic in `app.js`

### Modifying Styles
- Main styles: Edit `css/styles.css`
- Components: Edit `css/components.css`
- Use CSS custom properties for theming

### Adding JavaScript
- Configuration: Add to `config.js`
- Utilities: Add to `utils.js`
- Main logic: Add to `app.js`

## 🌐 Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile responsive design
- Progressive enhancement
- Graceful degradation

## 📦 Deployment

The static files are ready for production deployment:
- Minification ready
- CDN compatible
- Cache-friendly structure
- Optimized loading order

## 🔒 Security

- HTML sanitization for user content
- File type validation
- Size limits enforced
- XSS protection
- Input validation 