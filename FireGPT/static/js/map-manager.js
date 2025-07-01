// Map Manager for FireGPT - Enhanced Version with Sophisticated Location Extraction
class MapManager {
    constructor() {
        this.map = null;
        this.markers = [];
        this.fireIcon = null;
        this.emergencyIcon = null;
        this.weatherIcon = null;
        this.init();
    }

    init() {
        // Initialize the map when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.createMap());
        } else {
            this.createMap();
        }
    }

    createMap() {
        // Create the map instance
        this.map = L.map('map').setView([20, 0], 3);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);

        // Create custom icons
        this.createIcons();

        // Add some sample fire data
        this.addSampleData();

        console.log('Enhanced Map Manager initialized successfully');
    }

    createIcons() {
        // Fire icon
        this.fireIcon = L.divIcon({
            className: 'custom-fire-icon',
            html: '<i class="fas fa-fire" style="color: #ff4500; font-size: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);"></i>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        // Emergency icon
        this.emergencyIcon = L.divIcon({
            className: 'custom-emergency-icon',
            html: '<i class="fas fa-exclamation-triangle" style="color: #ff0000; font-size: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);"></i>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        // Weather icon
        this.weatherIcon = L.divIcon({
            className: 'custom-weather-icon',
            html: '<i class="fas fa-cloud-sun" style="color: #ffa500; font-size: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);"></i>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
    }

    addSampleData() {
        // Add some sample fire locations
        const sampleFires = [
            {
                name: "California Wildfire",
                lat: 36.7783,
                lng: -119.4179,
                type: "fire",
                severity: "high",
                description: "Active wildfire in California"
            },
            {
                name: "Australian Bushfire",
                lat: -25.2744,
                lng: 133.7751,
                type: "fire",
                severity: "medium",
                description: "Bushfire in Australia"
            },
            {
                name: "Amazon Rainforest Fire",
                lat: -3.4653,
                lng: -58.3804,
                type: "fire",
                severity: "high",
                description: "Deforestation fire in Amazon"
            }
        ];

        sampleFires.forEach(fire => {
            this.addFireMarker(fire);
        });
    }

    addFireMarker(fireData) {
        const icon = this.getIconForType(fireData.type);
        const marker = L.marker([fireData.lat, fireData.lng], { icon: icon })
            .addTo(this.map)
            .bindPopup(this.createPopupContent(fireData));

        // Store marker reference
        this.markers.push({
            marker: marker,
            data: fireData
        });

        return marker;
    }

    getIconForType(type) {
        switch (type) {
            case 'fire':
                return this.fireIcon;
            case 'emergency':
                return this.emergencyIcon;
            case 'weather':
                return this.weatherIcon;
            default:
                return this.fireIcon;
        }
    }

    createPopupContent(data) {
        const severityColor = this.getSeverityColor(data.severity);
        return `
            <div style="min-width: 200px;">
                <h3 style="margin: 0 0 8px 0; color: #333;">${data.name}</h3>
                <p style="margin: 0 0 8px 0; color: #666;">${data.description}</p>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="background: ${severityColor}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem;">
                        ${data.severity.toUpperCase()} SEVERITY
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 0.8rem; color: #888;">
                    Lat: ${data.lat.toFixed(4)}, Lng: ${data.lng.toFixed(4)}
                </div>
            </div>
        `;
    }

    getSeverityColor(severity) {
        switch (severity.toLowerCase()) {
            case 'low':
                return '#10b981';
            case 'medium':
                return '#f59e0b';
            case 'high':
                return '#ef4444';
            case 'extreme':
                return '#7c2d12';
            default:
                return '#6b7280';
        }
    }

    // Enhanced method to handle location data from LLM
    handleLocationData(locationData) {
        if (!locationData || !locationData.lat || !locationData.lng) {
            console.warn('Invalid location data received:', locationData);
            return;
        }

        // Add marker for the location
        const fireData = {
            name: locationData.name || "Fire Location",
            lat: locationData.lat,
            lng: locationData.lng,
            type: locationData.type || "fire",
            severity: locationData.severity || "medium",
            description: locationData.description || "Fire incident reported"
        };

        const marker = this.addFireMarker(fireData);

        // Fly to the location
        this.map.flyTo([locationData.lat, locationData.lng], 10, {
            duration: 1.5
        });

        // Open popup after animation
        setTimeout(() => {
            marker.openPopup();
        }, 1500);

        return marker;
    }

    // Enhanced method to search and add location by name with smart geocoding
    async searchAndAddLocation(locationName, fireData = {}) {
        try {
            const coordinates = await this.smartGeocodeLocation(locationName);
            if (coordinates) {
                const locationData = {
                    name: locationName,
                    lat: coordinates.lat,
                    lng: coordinates.lng,
                    type: fireData.type || "fire",
                    severity: fireData.severity || "medium",
                    description: fireData.description || `Fire incident at ${locationName}`
                };

                return this.handleLocationData(locationData);
            }
        } catch (error) {
            console.error('Error searching location:', error);
            return null;
        }
    }

    // Smart geocoding with multiple fallback strategies
    async smartGeocodeLocation(locationName) {
        // Strategy 1: Direct geocoding
        let coordinates = await this.geocodeLocation(locationName);
        if (coordinates) return coordinates;

        // Strategy 2: Try with "fire" keyword
        coordinates = await this.geocodeLocation(`${locationName} fire`);
        if (coordinates) return coordinates;

        // Strategy 3: Try with "wildfire" keyword
        coordinates = await this.geocodeLocation(`${locationName} wildfire`);
        if (coordinates) return coordinates;

        // Strategy 4: Try with "emergency" keyword
        coordinates = await this.geocodeLocation(`${locationName} emergency`);
        if (coordinates) return coordinates;

        // Strategy 5: Try with "incident" keyword
        coordinates = await this.geocodeLocation(`${locationName} incident`);
        if (coordinates) return coordinates;

        console.warn(`Could not geocode location: ${locationName}`);
        return null;
    }

    // Enhanced geocoding using OpenStreetMap Nominatim API
    async geocodeLocation(locationName) {
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationName)}&limit=1&addressdetails=1`
            );
            const data = await response.json();
            
            if (data && data.length > 0) {
                return {
                    lat: parseFloat(data[0].lat),
                    lng: parseFloat(data[0].lon)
                };
            }
            return null;
        } catch (error) {
            console.error('Geocoding error:', error);
            return null;
        }
    }

    // Reset map view to default
    resetView() {
        this.map.setView([20, 0], 3);
    }

    // Clear all markers
    clearMarkers() {
        this.markers.forEach(markerData => {
            this.map.removeLayer(markerData.marker);
        });
        this.markers = [];
    }

    // Get current map bounds
    getBounds() {
        return this.map.getBounds();
    }

    // Add weather data overlay (placeholder for future implementation)
    addWeatherOverlay() {
        // This could integrate with weather APIs to show wind patterns, temperature, etc.
        console.log('Weather overlay feature - to be implemented');
    }

    // Export map data
    exportMapData() {
        return this.markers.map(markerData => markerData.data);
    }
}

// Initialize enhanced map manager
window.mapManager = new MapManager();

// Enhanced function to extract locations from LLM responses
function extractLocationsFromResponse(response) {
    const locations = [];
    
    // Pattern 1: Structured mentions like "Location: X" or "Fire at X"
    const structuredPatterns = [
        /(?:location|fire|wildfire|incident)[:\s]+([^,\.\n]+)/gi,
        /(?:in|at|near|around)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/g,
        /(?:reported|detected|spreading)\s+(?:in|at|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/g
    ];

    // Pattern 2: Geographic entities (cities, states, countries, regions)
    const geographicPatterns = [
        /(?:city|town|village|state|province|country|region|area|district)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/gi,
        /([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:National\s+)?(?:Forest|Park|Reserve|Wilderness)/gi
    ];

    // Pattern 3: Coordinate patterns
    const coordinatePatterns = [
        /(\d+\.?\d*)\s*[°º]\s*[NSns]\s*,?\s*(\d+\.?\d*)\s*[°º]\s*[EWew]/g,
        /lat[:\s]*(\d+\.?\d*)[,\s]+lng[:\s]*(\d+\.?\d*)/gi
    ];

    // Pattern 4: Natural language descriptions
    const naturalLanguagePatterns = [
        /(?:there\s+is\s+a\s+fire|wildfire\s+is\s+burning|fire\s+has\s+broken\s+out)\s+(?:in|at|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/gi,
        /(?:fire\s+in|wildfire\s+in|blaze\s+in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/gi
    ];

    // Combine all patterns
    const allPatterns = [
        ...structuredPatterns,
        ...geographicPatterns,
        ...naturalLanguagePatterns
    ];

    // Extract locations using all patterns
    allPatterns.forEach(pattern => {
        let match;
        while ((match = pattern.exec(response)) !== null) {
            const location = match[1] || match[0];
            if (location && this.isValidLocation(location)) {
                locations.push({
                    name: location.trim(),
                    context: this.extractContext(response, match.index, 100)
                });
            }
        }
    });

    // Handle coordinate patterns separately
    coordinatePatterns.forEach(pattern => {
        let match;
        while ((match = pattern.exec(response)) !== null) {
            const lat = parseFloat(match[1]);
            const lng = parseFloat(match[2]);
            if (!isNaN(lat) && !isNaN(lng)) {
                locations.push({
                    coordinates: { lat, lng },
                    context: this.extractContext(response, match.index, 100)
                });
            }
        }
    });

    // Remove duplicates and return
    return this.removeDuplicateLocations(locations);
}

// Helper function to validate location names
function isValidLocation(locationName) {
    if (!locationName || locationName.length < 2) return false;
    
    // Filter out common non-location words
    const invalidWords = [
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'at', 'on', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'down', 'out', 'off', 'over', 'under', 'fire', 'wildfire',
        'blaze', 'burning', 'reported', 'detected', 'spreading', 'active', 'large',
        'small', 'major', 'minor', 'severe', 'extreme', 'high', 'medium', 'low'
    ];
    
    const words = locationName.toLowerCase().split(/\s+/);
    const validWords = words.filter(word => !invalidWords.includes(word));
    
    return validWords.length > 0 && locationName.length >= 3;
}

// Helper function to extract context around a match
function extractContext(text, index, contextLength) {
    const start = Math.max(0, index - contextLength);
    const end = Math.min(text.length, index + contextLength);
    return text.substring(start, end).trim();
}

// Helper function to remove duplicate locations
function removeDuplicateLocations(locations) {
    const seen = new Set();
    return locations.filter(location => {
        const key = location.name || `${location.coordinates?.lat},${location.coordinates?.lng}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
    });
}

// Helper function to extract severity from context
function extractSeverityFromContext(context) {
    const severityPatterns = [
        { pattern: /(?:severity|level)[:\s]*(low|medium|high|extreme)/i, severity: '$1' },
        { pattern: /(low|medium|high|extreme)\s+severity/i, severity: '$1' },
        { pattern: /(?:very\s+)?(severe|extreme|critical)/i, severity: 'high' },
        { pattern: /(?:minor|small|contained)/i, severity: 'low' },
        { pattern: /(?:major|large|out\s+of\s+control)/i, severity: 'high' }
    ];

    for (const { pattern, severity } of severityPatterns) {
        const match = context.match(pattern);
        if (match) {
            return severity === '$1' ? match[1].toLowerCase() : severity;
        }
    }
    
    return 'medium'; // default severity
}

// Enhanced global function to handle LLM responses with sophisticated location extraction
window.handleLLMLocationResponse = function(response) {
    console.log('Processing LLM response for locations:', response);
    
    // Extract all locations from the response
    const locations = extractLocationsFromResponse(response);
    
    if (locations.length === 0) {
        console.log('No locations found in response');
        return;
    }

    console.log(`Found ${locations.length} location(s):`, locations);

    // Process each location with a delay to avoid overwhelming the map
    locations.forEach((location, index) => {
        setTimeout(async () => {
            try {
                if (location.coordinates) {
                    // Direct coordinates provided
                    const severity = extractSeverityFromContext(location.context);
                    const fireData = {
                        name: `Fire Location ${index + 1}`,
                        lat: location.coordinates.lat,
                        lng: location.coordinates.lng,
                        type: "fire",
                        severity: severity,
                        description: `Fire incident at coordinates ${location.coordinates.lat}, ${location.coordinates.lng}`
                    };
                    mapManager.handleLocationData(fireData);
                } else if (location.name) {
                    // Location name provided - use smart geocoding
                    const severity = extractSeverityFromContext(location.context);
                    await mapManager.searchAndAddLocation(location.name, {
                        severity: severity,
                        description: `Fire incident reported at ${location.name}`
                    });
                }
            } catch (error) {
                console.error(`Error processing location ${index + 1}:`, error);
            }
        }, index * 1000); // 1 second delay between each location
    });
}; 