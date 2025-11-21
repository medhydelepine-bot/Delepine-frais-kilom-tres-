<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Delepine Domicile Services</title>
    
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.css" />
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">

    <style>
        body { font-family: 'Poppins', sans-serif; margin: 0; padding: 0; display: flex; height: 100vh; background-color: #f0f2f5; }
        
        #sidebar { width: 350px; background: white; padding: 20px; box-shadow: 2px 0 10px rgba(0,0,0,0.1); z-index: 1000; display: flex; flex-direction: column; gap: 15px; overflow-y: auto; }
        
        .brand-header { display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 15px; }
        .logo-container { width: 140px; height: 140px; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; }
        .logo-img { width: 100%; height: 100%; object-fit: contain; border-radius: 50%; }
        
        .start-address { color: #7f8c8d; font-size: 0.8rem; margin-top: 8px; font-style: italic; }

        .search-box { display: flex; gap: 5px; }
        input { flex-grow: 1; padding: 12px; border: 2px solid #eee; border-radius: 8px; outline: none; font-family: inherit; -webkit-appearance: none; }
        input:focus { border-color: #3498db; }
        button { padding: 0 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
        button:hover { background: #2980b9; }

        #result-card { background: #ecf0f1; border-radius: 12px; padding: 15px; text-align: center; display: none; animation: popIn 0.5s ease; border-left: 5px solid #ccc; }
        .price-tag { font-size: 2.5rem; font-weight: bold; color: #27ae60; margin: 5px 0; }
        
        .details { font-size: 0.9rem; color: #555; text-align: left; margin-top: 10px; border-top: 1px solid #ccc; padding-top: 10px; }
        .details p { margin: 8px 0; display: flex; justify-content: space-between; }
        
        .zone-badge { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; color: white; font-weight: bold; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; }
        
        /* Changement ici : couleur de fond un peu plus chaude si la carte charge mal */
        #map { flex-grow: 1; height: 100%; cursor: crosshair; background: #fcfcfc; }
        @keyframes popIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        .legend { font-size: 0.75rem; background: #fff; padding: 10px; border-radius: 8px; border: 1px solid #eee; margin-top: auto; }
        .legend-title { font-weight: bold; display: block; margin-bottom: 5px; }
        .legend-item { display: flex; justify-content: space-between; margin-bottom: 3px; color: #555; }
        .legend-color { width: 12px; height: 12px; display: inline-block; margin-right: 5px; border-radius: 50%; }
        
        #loading-zone { font-size: 0.7rem; color: orange; text-align: center; display: none; }
    </style>
</head>
<body>

    <div id="sidebar">
        <div class="brand-header">
            <div class="logo-container">
                <img src="logo.png" alt="Logo Delepine" class="logo-img">
            </div>
            <div class="start-address">📍 Siège : 21 rue Paul Bert, 59950 Auby</div>
            <div id="loading-zone">Chargement des zones réelles...</div>
        </div>

        <div class="search-box">
            <input type="text" id="addressInput" placeholder="Adresse ou cliquez sur la carte..." onkeypress="handleEnter(event)">
            <button onclick="searchAddress()">GO</button>
        </div>

        <div id="result-card">
            <div id="zoneLabel" class="zone-badge">--</div>
            <div>Total Prestation</div>
            <div id="finalPrice" class="price-tag">0 €</div>
            
            <div class="details">
                <p><span>⏱️ Temps trajet :</span> <strong id="timeDisplay">-- min</strong></p>
                <p><span>📏 Distance réelle :</span> <strong id="distanceDisplay">-- km</strong></p>
                <p><span>💼 Base prestation :</span> <strong>25,00 €</strong></p>
                <p><span>⛽ Supplément km :</span> <strong id="feeDisplay">-- €</strong></p>
            </div>
        </div>

        <div class="legend">
            <span class="legend-title">Barème (Km Réel parcouru)</span>
            <div class="legend-item"><div><span class="legend-color" style="background:#2ecc71"></span>0 - 10 km</div> <span>Inclus (0€)</span></div>
            <div class="legend-item"><div><span class="legend-color" style="background:#f1c40f"></span>10 - 15 km</div> <span>+ 1,50 €</span></div>
            <div class="legend-item"><div><span class="legend-color" style="background:#e67e22"></span>15 - 20 km</div> <span>+ 3,00 €</span></div>
            <div class="legend-item"><div><span class="legend-color" style="background:#d35400"></span>20 - 25 km</div> <span>+ 4,50 €</span></div>
            <div class="legend-item"><div><span class="legend-color" style="background:#c0392b"></span>25 - 30 km</div> <span>+ 6,00 €</span></div>
        </div>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.js"></script>
    
    <script>
        // ===========================================================
        // 🔑 CONFIGURATION DE LA CLE API (OBLIGATOIRE POUR LES ZONES)
        // ===========================================================
         const ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0=";
        // ===========================================================

        const HOME_COORDS = [50.4137, 3.0568]; // Auby
        var map = L.map('map').setView(HOME_COORDS, 10);

        // --- NOUVEAU FOND DE CARTE (PLUS VIF ET LUDIQUE) ---
        // Utilisation des tuiles Esri World Street Map pour des couleurs plus chaudes
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
	        attribution: 'Tiles © Esri',
            opacity: 0.85 // Opacité augmentée pour que ce soit plus vif, mais en laissant voir un peu les zones
        }).addTo(map);

        var homeIcon = L.icon({
            iconUrl: 'https://cdn-icons-png.flaticon.com/512/25/25694.png',
            iconSize: [30, 30]
        });
        L.marker(HOME_COORDS, {icon: homeIcon}).addTo(map).bindPopup("<b>Siège Delepine</b>").openPopup();

        // --- FONCTION D'AFFICHAGE DES ZONES REELLES (ISOCHRONES) ---
        function drawIsochrones() {
            if(ORS_API_KEY === "VOTRE_CLE_ICI") {
                console.warn("Attention: Clé API manquante pour les zones.");
                return;
            }

            document.getElementById('loading-zone').style.display = 'block';

            var ranges = [30000, 25000, 20000, 15000, 10000]; 
            
            fetch("https://api.openrouteservice.org/v2/isochrones/driving-car", {
                method: 'POST',
                headers: {
                    'Authorization': ORS_API_KEY,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    "locations": [[HOME_COORDS[1], HOME_COORDS[0]]],
                    "range": ranges,
                    "range_type": "distance",
                    "units": "m",
                    "smoothing": 5
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('loading-zone').style.display = 'none';
                
                L.geoJSON(data, {
                    style: function(feature) {
                        var val = feature.properties.value;
                        var col = "#7f8c8d";
                        
                        if (val <= 10000) col = "#2ecc71";
                        else if (val <= 15000) col = "#f1c40f";
                        else if (val <= 20000) col = "#e67e22";
                        else if (val <= 25000) col = "#d35400";
                        else col = "#c0392b";

                        return {
                            color: col,
                            weight: 1,
                            fillColor: col,
                            // J'ai légèrement augmenté l'opacité des zones aussi pour qu'elles ne soient pas "mangées" par le nouveau fond
                            fillOpacity: 0.15, 
                            interactive: false
                        };
                    }
                }).addTo(map);
            })
            .catch(err => {
                console.error("Erreur chargement zones", err);
                document.getElementById('loading-zone').innerText = "Erreur API Zones";
            });
        }

        drawIsochrones();

        // --- GESTION ITINERAIRE ---
        var routingControl = null;
        var destMarker = null;

        map.on('click', function(e) {
            var lat = e.latlng.lat;
            var lon = e.latlng.lng;
            calculateRoute(lat, lon);
            fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`)
                .then(response => response.json())
                .then(data => {
                    if(data && data.display_name) {
                        let shortName = data.display_name.split(',').slice(0, 3).join(',');
                        document.getElementById('addressInput').value = shortName;
                    }
                });
        });

        function handleEnter(e) { if(e.key === 'Enter') searchAddress(); }

        async function searchAddress() {
            var address = document.getElementById('addressInput').value;
            if (!address) return alert("Veuillez entrer une adresse.");
            try {
                let response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`);
                let data = await response.json();
                if (data.length === 0) { return alert("Adresse introuvable."); }
                calculateRoute(data[0].lat, data[0].lon);
            } catch (error) { alert("Erreur réseau."); }
        }

        function calculateRoute(lat, lon) {
            if (routingControl) map.removeControl(routingControl);
            if (destMarker) map.removeLayer(destMarker);

            destMarker = L.marker([lat, lon]).addTo(map);

            routingControl = L.Routing.control({
                waypoints: [L.latLng(HOME_COORDS), L.latLng(lat, lon)],
                routeWhileDragging: false, show: false, addWaypoints: false,
                // Ligne de trajet un peu plus épaisse et foncée pour bien ressortir
                lineOptions: { styles: [{color: '#2c3e50', opacity: 0.9, weight: 6}] }, 
                createMarker: function() { return null; }
            }).addTo(map);

            routingControl.on('routesfound', function(e) {
                var routes = e.routes[0];
                var summary = routes.summary;
                updatePrice((summary.totalDistance / 1000).toFixed(1), Math.round(summary.totalTime / 60));
            });
        }

        function updatePrice(km, time) {
            const BASE = 25.00;
            let fee = 0;
            let color = "#2ecc71";
            let label = "Zone 1 (0-10km)";
            let dist = parseFloat(km);

            if (dist <= 10) { fee = 0; color = "#2ecc71"; label = "Zone Gratuite"; }
            else if (dist <= 15) { fee = 1.50; color = "#f1c40f"; label = "Zone 2 (10-15km)"; }
            else if (dist <= 20) { fee = 3.00; color = "#e67e22"; label = "Zone 3 (15-20km)"; }
            else if (dist <= 25) { fee = 4.50; color = "#d35400"; label = "Zone 4 (20-25km)"; }
            else if (dist <= 30) { fee = 6.00; color = "#c0392b"; label = "Zone 5 (25-30km)"; }
            else { fee = 6.00; color = "#7f8c8d"; label = "Hors Zone (>30km)"; }

            let card = document.getElementById('result-card');
            card.style.display = 'block';
            card.style.borderLeftColor = color;
            
            document.getElementById('timeDisplay').innerText = time + " min";
            document.getElementById('distanceDisplay').innerText = dist + " km";
            document.getElementById('feeDisplay').innerText = "+" + fee.toFixed(2) + " €";
            document.getElementById('finalPrice').innerText = (BASE + fee).toFixed(2) + " €";
            document.getElementById('finalPrice').style.color = color;
            
            let badge = document.getElementById('zoneLabel');
            badge.innerText = label;
            badge.style.backgroundColor = color;
        }
    </script>
</body>
</html>
