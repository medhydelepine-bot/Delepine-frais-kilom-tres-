import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 🔑 CONFIGURATION
# =========================================================
# Votre clé API (Intégrée)
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# Vos coordonnées EXACTES (Auby)
HOME_COORDS = [50.414771, 3.056326]

# Configuration de la page (Plein écran)
st.set_page_config(page_title="Delepine Domicile", page_icon="📍", layout="wide")

# =========================================================
# 🎨 DESIGN CSS (STYLE GOOGLE MAPS + RÉSUMÉ PROPRE)
# =========================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* 1. CARTE PLEIN ÉCRAN (On enlève les marges) */
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    header, footer { visibility: hidden; }

    /* 2. SIDEBAR (Style Panneau Latéral Google) */
    [data-testid="stSidebar"] {
        background-color: white;
        box-shadow: 4px 0 15px rgba(0,0,0,0.1);
        border-right: none;
        padding-top: 10px;
        width: 400px !important;
        z-index: 1000;
    }

    /* 3. LE RÉSUMÉ (La fameuse carte qui ne s'affichait plus) */
    .result-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    .price-big {
        color: #1a73e8; /* Bleu Google */
        font-size: 2.8rem;
        font-weight: 700;
        margin: 5px 0;
    }

    .badge-zone {
        background: #e8f0fe;
        color: #1967d2;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #f1f3f4;
        font-size: 0.95rem;
        color: #3c4043;
    }
    .stat-row:last-child { border-bottom: none; }

    /* 4. BOUTONS ET CHAMPS */
    div.stButton > button {
        background-color: #1a73e8;
        color: white;
        border-radius: 24px;
        border: none;
        padding: 10px 0;
        font-weight: 500;
        width: 100%;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        background-color: #1557b0;
    }

    div[data-baseweb="input"] {
        border-radius: 24px;
        border: 1px solid #dadce0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLIENT API ---
client = None
if ORS_API_KEY:
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
    except: pass

# --- ETAT (MÉMOIRE) ---
if 'route_data' not in st.session_state: st.session_state.route_data = None
if 'last_coords' not in st.session_state: st.session_state.last_coords = None

# --- LOGIQUE CALCUL ---
def calculate_price_tier(km):
    base_price = 25.00
    fee = 0
    label = "HORS ZONE"
    
    if km <= 10:   fee = 0;    label = "Zone 1" 
    elif km <= 15: fee = 1.50; label = "Zone 2" 
    elif km <= 20: fee = 3.00; label = "Zone 3" 
    elif km <= 25: fee = 4.50; label = "Zone 4" 
    elif km <= 30: fee = 6.00; label = "Zone 5" 
    else:          fee = 6.00; label = "> 30km"
        
    return { "total": base_price + fee, "fee": fee, "label": label }

@st.cache_data
def get_isochrones():
    if not client: return None
    try:
        return client.isochrones(
            locations=[[HOME_COORDS[1], HOME_COORDS[0]]],
            range=[30000, 25000, 20000, 15000, 10000],
            range_type="distance", units="m", smoothing=5
        )
    except: return None

def get_route(dest_lat, dest_lon):
    if not client: return None
    try:
        coords = [[HOME_COORDS[1], HOME_COORDS[0]], [dest_lon, dest_lat]]
        routes = client.directions(coordinates=coords, profile='driving-car', format='geojson')
        summary = routes['features'][0]['properties']['summary']
        dist_km = round(summary['distance'] / 1000, 1)
        duration_min = round(summary['duration'] / 60)
        geometry = routes['features'][0]['geometry']['coordinates']
        decoded_geom = [(lat, lon) for lon, lat in geometry]
        return { "dist_km": dist_km, "duration_min": duration_min, "geometry": decoded_geom, "price_info": calculate_price_tier(dist_km) }
    except: return None

# =========================================================
# 📱 SIDEBAR (PANNEAU DE CONTRÔLE)
# =========================================================
with st.sidebar:
    # En-tête
    c1, c2 = st.columns([1, 4])
    with c1:
        try: st.image("logo.png", width=60)
        except: st.write("📍")
    with c2:
        st.markdown("<h3 style='margin:0; color:#202124;'>Delepine</h3>", unsafe_allow_html=True)
        st.markdown("<p style='margin:0; color:#5f6368; font-size:0.9rem;'>Domicile Services</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Recherche
    addr = st.text_input("Saisissez une adresse", placeholder="Rechercher dans Google Maps...")
    if st.button("Calculer l'itinéraire") and addr and client:
        try:
            geo = client.pelias_search(text=addr, focus_point=[HOME_COORDS[1], HOME_COORDS[0]])
            if geo['features']:
                c = geo['features'][0]['geometry']['coordinates']
                st.session_state.last_coords = [c[1], c[0]]
                st.session_state.route_data = get_route(c[1], c[0])
            else:
                st.error("Lieu introuvable")
        except:
            st.error("Erreur technique API")

    # --- C'EST ICI QUE LE RÉSUMÉ S'AFFICHE ---
    if st.session_state.route_data:
        d = st.session_state.route_data
        i = d['price_info']
        
        st.markdown(f"""
        <div class="result-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span class="badge-zone">{i['label']}</span>
                <span style="font-size:0.8rem; color:#5f6368;">TTC</span>
            </div>
            
            <div class="price-big">{i['total']:.2f} €</div>
            
            <div style="margin-top:20px;">
                <div class="stat-row">
                    <span>⏱️ Durée estimée</span>
                    <strong>{d['duration_min']} min</strong>
                </div>
                <div class="stat-row">
                    <span>🚗 Distance</span>
                    <strong>{d['dist_km']} km</strong>
                </div>
                <div class="stat-row">
                    <span>⛽ Frais km</span>
                    <strong>+{i['fee']} €</strong>
                </div>
                <div class="stat-row">
                    <span>💼 Forfait base</span>
                    <strong>25.00 €</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Message par défaut
        st.markdown("""
        <div style="margin-top: 50px; text-align: center; color: #9aa0a6;">
            <div style="font-size: 2rem; margin-bottom: 10px;">🗺️</div>
            <p>Sélectionnez une destination sur la carte.</p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# 🗺️ CARTE PLEIN ÉCRAN
# =========================================================

m = folium.Map(
    location=HOME_COORDS, 
    zoom_start=12, 
    tiles='https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', 
    attr='CartoDB Voyager'
)

# Zones
iso = get_isochrones()
if iso:
    def style_zones(feature):
        v = feature['properties']['value']
        c = "#9aa0a6"
        if v <= 10000: c = "#34a853"   # Vert
        elif v <= 15000: c = "#4285f4" # Bleu
        elif v <= 20000: c = "#fbbc05" # Jaune
        elif v <= 25000: c = "#ea4335" # Rouge
        elif v <= 30000: c = "#b01c10" # Rouge Foncé
        return { 'fillColor': c, 'color': c, 'weight': 1, 'fillOpacity': 0.15, 'interactive': False }
    folium.GeoJson(iso, style_function=style_zones).add_to(m)

# Marqueur Maison
folium.CircleMarker(
    location=HOME_COORDS, radius=8, color='#1a73e8', fill=True, fill_color='#4285f4', fill_opacity=1, popup="Siège"
).add_to(m)

# Trajet
if st.session_state.route_data:
    folium.PolyLine(
        st.session_state.route_data['geometry'], 
        color="#1a73e8", weight=6, opacity=0.8
    ).add_to(m)
    folium.Marker(
        st.session_state.last_coords, 
        icon=folium.Icon(color="red", icon="map-marker", prefix="fa")
    ).add_to(m)

# Rendu Carte
out = st_folium(m, width="100%", height=900) # Hauteur fixe pour bien remplir l'écran

# Gestion Clic
if out['last_clicked']:
    clat, clon = out['last_clicked']['lat'], out['last_clicked']['lng']
    same = False
    if st.session_state.last_coords and abs(st.session_state.last_coords[0] - clat) < 0.0001: same = True
    
    if not same:
        st.session_state.last_coords = [clat, clon]
        st.session_state.route_data = get_route(clat, clon)
        st.rerun()
