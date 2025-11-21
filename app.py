import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 🔑 CONFIGURATION
# =========================================================
# Ta clé API (intégrée)
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# Coordonnées EXACTES (Maison)
HOME_COORDS = [50.414771, 3.056326]

# Configuration de la page en mode "Large" pour prendre tout l'écran
st.set_page_config(page_title="Delepine Domicile", page_icon="📍", layout="wide")

# =========================================================
# 🎨 DESIGN CSS "GOOGLE MAPS STYLE"
# =========================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* 1. LA CARTE EN PLEIN ÉCRAN (Suppression des marges Streamlit) */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        margin: 0 !important;
    }
    
    /* On cache le header Streamlit et le footer pour l'immersion */
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* 2. LE PANNEAU LATÉRAL (Transformé en Card Flottante) */
    [data-testid="stSidebar"] {
        background-color: white;
        box-shadow: 2px 0 15px rgba(0,0,0,0.15); /* Ombre portée douce */
        border-right: none;
        padding-top: 20px;
        z-index: 99999; /* Toujours au dessus */
        width: 400px !important; /* Largeur fixe type Google Maps */
    }
    
    /* Titre Application */
    .app-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #202124; /* Noir Google */
        margin-bottom: 5px;
    }
    
    .app-subtitle {
        font-size: 0.9rem;
        color: #5f6368; /* Gris Google */
        margin-bottom: 20px;
    }

    /* 3. CHAMPS DE RECHERCHE (Style Material Design) */
    div[data-baseweb="input"] {
        background-color: white;
        border: 1px solid #dadce0;
        border-radius: 24px; /* Arrondi fort comme Google */
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* 4. BOUTONS (Bleu Google) */
    div.stButton > button {
        background-color: #1a73e8;
        color: white;
        border-radius: 24px;
        border: none;
        padding: 10px 24px;
        font-weight: 500;
        text-transform: none; /* Pas de majuscules forcées */
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #1557b0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    /* 5. CARTES DE RÉSULTATS (Propres et blanches) */
    .result-card {
        background: #fff;
        border: 1px solid #dadce0;
        border-radius: 8px;
        padding: 16px;
        margin-top: 20px;
    }
    
    .price-big {
        color: #1a73e8;
        font-size: 2.5rem;
        font-weight: 400;
    }
    
    .badge-zone {
        background: #e8f0fe;
        color: #1967d2;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #f1f3f4;
        font-size: 0.9rem;
        color: #3c4043;
    }
    .stat-row:last-child { border-bottom: none; }

    </style>
    """, unsafe_allow_html=True)

# --- CONFIG API ---
client = None
if ORS_API_KEY:
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
    except: pass

# --- ETAT ---
if 'route_data' not in st.session_state: st.session_state.route_data = None
if 'last_coords' not in st.session_state: st.session_state.last_coords = None

# --- LOGIQUE MÉTIER ---
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
# 📱 BARRE LATÉRALE (Le Panneau de Contrôle)
# =========================================================
with st.sidebar:
    # Logo et Titre épurés
    col_a, col_b = st.columns([1, 4])
    with col_a:
        try: st.image("logo.png", width=50)
        except: st.write("📍")
    with col_b:
        st.markdown('<div class="app-title">Delepine</div>', unsafe_allow_html=True)
        st.markdown('<div class="app-subtitle">Services à domicile • Auby</div>', unsafe_allow_html=True)

    # Recherche
    addr = st.text_input("Saisissez une adresse", placeholder="Rechercher dans Google Maps...")
    
    if st.button("Itinéraire") and addr and client:
        try:
            geo = client.pelias_search(text=addr, focus_point=[HOME_COORDS[1], HOME_COORDS[0]])
            if geo['features']:
                c = geo['features'][0]['geometry']['coordinates']
                st.session_state.last_coords = [c[1], c[0]]
                st.session_state.route_data = get_route(c[1], c[0])
            else:
                st.error("Lieu introuvable")
        except:
            st.error("Erreur technique")

    # Résultats style "Fiche Lieu"
    if st.session_state.route_data:
        d = st.session_state.route_data
        i = d['price_info']
        
        st.markdown("---")
        st.markdown(f"""
        <div class="result-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="badge-zone">{i['label']}</span>
                <span style="font-size:0.8rem; color:#5f6368;">TTC</span>
            </div>
            <div class="price-big">{i['total']:.2f} €</div>
            
            <div style="margin-top:15px;">
                <div class="stat-row">
                    <span>🚗 Distance routière</span>
                    <strong>{d['dist_km']} km</strong>
                </div>
                <div class="stat-row">
                    <span>⏱️ Durée estimée</span>
                    <strong>{d['duration_min']} min</strong>
                </div>
                <div class="stat-row">
                    <span>⛽ Frais kilométriques</span>
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
        st.markdown("""
        <div style="margin-top: 50px; text-align: center; color: #9aa0a6;">
            <p>Sélectionnez un point sur la carte<br>ou cherchez une adresse.</p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# 🗺️ LA CARTE (Fond d'écran interactif)
# =========================================================

# On utilise CartoDB Positron pour un fond très clair et propre, style "Maps"
m = folium.Map(
    location=HOME_COORDS, 
    zoom_start=12, 
    tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', 
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    control_scale=True
)

# Zones (Couleurs Google : Rouge, Bleu, Jaune, Vert)
iso = get_isochrones()
if iso:
    def style_zones(feature):
        v = feature['properties']['value']
        c = "#9aa0a6"
        # Palette Google Colors
        if v <= 10000: c = "#34a853"   # Green
        elif v <= 15000: c = "#4285f4" # Blue
        elif v <= 20000: c = "#fbbc05" # Yellow
        elif v <= 25000: c = "#ea4335" # Red
        elif v <= 30000: c = "#b01c10" # Dark Red
        
        return { 
            'fillColor': c, 
            'color': c, 
            'weight': 1, 
            'fillOpacity': 0.15, # Léger pour voir les rues
            'interactive': False 
        }
    folium.GeoJson(iso, style_function=style_zones).add_to(m)

# Marqueur Maison (Simple point bleu avec cercle blanc comme "Ma position")
folium.CircleMarker(
    location=HOME_COORDS,
    radius=8,
    color='#1a73e8',
    fill=True,
    fill_color='#4285f4',
    fill_opacity=1,
    popup="Siège"
).add_to(m)

# Trajet
if st.session_state.route_data:
    folium.PolyLine(
        st.session_state.route_data['geometry'], 
        color="#1a73e8", # Bleu itinéraire Google
        weight=6, 
        opacity=0.8
    ).add_to(m)
    
    # Marqueur Arrivée (Pin Rouge Classique)
    folium.Marker(
        st.session_state.last_coords, 
        icon=folium.Icon(color="red", icon="map-marker", prefix="fa")
    ).add_to(m)

# Rendu de la carte en PLEIN ÉCRAN
# Note : on force la hauteur à 100vh (hauteur de l'écran)
out = st_folium(m, width="100%", height=1000) 

# Gestion du Clic sur la carte
if out['last_clicked']:
    clat, clon = out['last_clicked']['lat'], out['last_clicked']['lng']
    # Anti-rebond
    same = False
    if st.session_state.last_coords and abs(st.session_state.last_coords[0] - clat) < 0.0001: same = True
    
    if not same:
        st.session_state.last_coords = [clat, clon]
        st.session_state.route_data = get_route(clat, clon)
        st.rerun()
