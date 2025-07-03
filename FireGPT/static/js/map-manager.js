// Map Manager for FireGPT - Cleaned Version
class MapManager {
    constructor() {
        this.map = null;
        this.markers = [];
        this.fireIcon = null;
        this.emergencyIcon = null;
        this.weatherIcon = null;
        this.placingFire = false;
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.createMap());
        } else {
            this.createMap();
        }
    }

    createMap() {
        this.map = L.map('map').setView([20, 0], 3);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Â© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);

        this.createIcons();
        this.addSampleData();

        // Click listener for manual fire placement
        // In the createMap() function, modify the click handler:
        this.map.on('click', (e) => {
            if (!this.placingFire) return;
            this.placingFire = false;

            const { lat, lng } = e.latlng;
            this.clearMarkers();

            fetch("/plan_action", {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ latitude: lat, longitude: lng })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    displayBotMessage("An error occurred: " + data.error);
                    return;
                }

                displayBotMessage("🔥 **Fire Action Plan**\n\n" + data.plan);
                
                // Add fire marker
                this.addMarker(data.markers.fire.lat, data.markers.fire.lon, "🔥 Fire Location", this.fireIcon);
                
                // Add other markers with appropriate icons
                data.markers.crews.forEach(crew => {
                    this.addMarker(crew.lat, crew.lon, "🚒 Fire Station", this.emergencyIcon);
                });
                
                data.markers.hospitals.forEach(hospital => {
                    this.addMarker(hospital.lat, hospital.lon, "🏥 Hospital", this.emergencyIcon);
                });
                
                data.markers.water_sources.forEach(water => {
                    this.addMarker(water.lat, water.lon, "💧 Water Source", this.weatherIcon);
                });
                
                data.markers.safe_zones.forEach(zone => {
                    this.addMarker(zone.lat, zone.lon, "🛡️ Safe Zone", this.emergencyIcon);
                });
            })
            .catch(err => {
                console.error("Request failed:", err);
                displayBotMessage("A critical error occurred while fetching the action plan.");
            });
        });

    }

    createIcons() {
        this.fireIcon = L.divIcon({
            className: 'custom-fire-icon',
            html: '<i class="fas fa-fire" style="color:#ff4500;font-size:20px;"></i>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        this.emergencyIcon = L.divIcon({
            className: 'custom-emergency-icon',
            html: '<i class="fas fa-exclamation-triangle" style="color:#ff0000;font-size:20px;"></i>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        this.weatherIcon = L.divIcon({
            className: 'custom-weather-icon',
            html: '<i class="fas fa-cloud-sun" style="color:#ffa500;font-size:20px;"></i>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        // Add new icons
        this.waterIcon = L.divIcon({
            className: 'custom-water-icon',
            html: '<i class="fas fa-tint" style="color:#1e90ff;font-size:20px;"></i>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        this.hospitalIcon = L.divIcon({
            className: 'custom-hospital-icon',
            html: '<i class="fas fa-hospital" style="color:#ff0000;font-size:20px;"></i>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });

        this.safeZoneIcon = L.divIcon({
            className: 'custom-safe-zone-icon',
            html: '<i class="fas fa-shield-alt" style="color:#32cd32;font-size:20px;"></i>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
    }

    addSampleData() {
        const samples = [
            { name: "California Wildfire", lat: 36.7783, lng: -119.4179, type: "fire", severity: "high", description: "Active wildfire in California" },
            { name: "Australian Bushfire", lat: -25.2744, lng: 133.7751, type: "fire", severity: "medium", description: "Bushfire in Australia" },
            { name: "Amazon Rainforest Fire", lat: -3.4653, lng: -58.3804, type: "fire", severity: "high", description: "Deforestation fire in Amazon" }
        ];
        samples.forEach(f => this.addFireMarker(f));
    }

    addFireMarker(data) {
        const marker = L.marker([data.lat, data.lng], { icon: this.getIconForType(data.type) })
            .addTo(this.map)
            .bindPopup(this.createPopupContent(data));
        this.markers.push({ marker, data });
        return marker;
    }

    addMarker(lat, lng, label, icon) {
        const m = L.marker([lat, lng], { icon }).addTo(this.map).bindPopup(label).openPopup();
        this.markers.push({ marker: m });
    }

    getIconForType(type) {
        switch (type) {
            case 'fire': return this.fireIcon;
            case 'emergency': return this.emergencyIcon;
            case 'weather': return this.weatherIcon;
            default: return this.fireIcon;
        }
    }

    createPopupContent(data) {
        const color = this.getSeverityColor(data.severity);
        return `
            <div style="min-width:200px;">
                <h3>${data.name}</h3>
                <p>${data.description}</p>
                <span style="background:${color};color:white;padding:4px 8px;border-radius:8px;">${data.severity.toUpperCase()}</span>
                <div style="margin-top:8px;font-size:0.8rem;">Lat: ${data.lat.toFixed(4)}, Lng: ${data.lng.toFixed(4)}</div>
            </div>
        `;
    }

    getSeverityColor(sev) {
        switch (sev) {
            case 'low': return '#10b981';
            case 'medium': return '#f59e0b';
            case 'high': return '#ef4444';
            case 'extreme': return '#7c2d12';
            default: return '#6b7280';
        }
    }

    resetView() { this.map.setView([20, 0], 3); }
    clearMarkers() { this.markers.forEach(m => this.map.removeLayer(m.marker)); this.markers = []; }
    enableFirePlacement() { this.placingFire = true; alert("Click on the map to place a fire location."); }
}

window.mapManager = new MapManager();