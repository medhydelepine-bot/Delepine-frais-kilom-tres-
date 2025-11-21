import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 🔑 CONFIGURATION
# =========================================================
# ⚠️ COLLEZ VOTRE CLÉ API CI-DESSOUS
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# Coordonnées EXACTES (Maison)
HOME_COORDS = [50.414771, 3.056326]
# =========================================================

st.set_page_config(page_title="Delepine Domicile", page_icon="🏡", layout="wide")

# =========================================================
# 🎨 DESIGN & CSS (C'est ici que la magie visuelle opère)
# =========================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* Style de la Sidebar pour faire "App Pro" */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }

    /* La Carte de Prix Principale */
    .main-card {
        background: white;
        border-radius: 20px;
        padding: 25px 15px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        transition: transform 0.3s ease;
        margin-bottom: 20px;
        border: 1px solid #f0f0f0;
    }
    
    .main-card:hover {
        transform: translateY(-5px);
    }

    /* Le Gros Prix */
    .price-display {
        font-size: 3.5rem;
        font-weight: 800;
        margin: 10px 0;
        letter-spacing: -1px;
    }

    /* Le Badge de Zone */
    .zone-pill {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 50px;
        color: white;
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    /* Grille pour les détails (Temps, Km, Extra) */
    .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 10px;
        margin-top: 20px;
    }

    .stat-box {
        background: #f1f3f5;
        padding: 10px 5px;
        border-radius: 12px;
        text-align: center;
    }

    .stat-icon { font-size: 1.2rem; margin-bottom: 5px; display:block; }
    .stat-val { font-weight: 700; font-size: 0.9rem; color: #343a40; display:block; }
    .stat-label { font-size: 0.65rem; color: #868e96; text-transform: uppercase; display:block; }

    /* Bouton personnalisé */
    div.stButton > button {
        width: 100%;
        background-color: #2c3e50;
        color: white;
        border-radius: 12px;
        padding: 10px 0;
        font-weight: 600;
        border: none;
        transition: background 0.2s;
    }
    div.stButton > button:hover {
        background-color: #1a252f;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLIENT API ---
client = None
if ORS_API_KEY and ORS_API_KEY != "VOTRE_CLE_API_ICI":
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
    except:
        st.error("⚠️ Clé API non configurée")

# --- ETAT ---
if 'route_data' not in st.session_state: st.session_state.route_data = None
if 'last_coords' not in st.session_state: st.session_state.last_coords = None

# --- LOGIQUE ---
def calculate_price_tier(km):
    base_price = 25.00
    fee = 0
    # Couleurs "Material Design" vibrantes
    color = "#636e72"
    label = "HORS ZONE"
    
    if km <= 10:   fee = 0;    color = "#00b894"; label = "Zone 1" # Mint
    elif km <= 15: fee = 1.50; color = "#0984e3"; label = "Zone 2" # Electron Blue
    elif km <= 20: fee = 3.00; color = "#fdcb6e"; label = "Zone 3" # Mustard
    elif km <= 25: fee = 4.50; color = "#e056fd"; label = "Zone 4" # Pink/Purple
    elif km <= 30: fee = 6.00; color = "#d63031"; label = "Zone 5" # Red
    else:          fee = 6.00; color = "#2d3436"; label = "> 30km"
        
    return { "total": base_price + fee, "fee": fee, "color": color, "label": label }

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
# 📱 INTERFACE SIDEBAR (Type App Mobile)
# =========================================================
with st.sidebar:
    # En-tête centré avec logo
    col_l, col_m, col_r = st.columns([1,2,1])
    with col_m:
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.markdown("## 🏠")
    
    st.markdown("<h3 style='text-align: center; margin-bottom: 0;'>Delepine Services</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888; font-size: 0.8rem;'>📍 Départ : Auby</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Zone de Recherche
    with st.container():
        addr = st.text_input("Rechercher un client...", placeholder="Ex: 10 rue de la Gare, Douai")
        if st.button("CALCULER L'ITINÉRAIRE") and addr and client:
            try:
                geo = client.pelias_search(text=addr, focus_point=[HOME_COORDS[1], HOME_COORDS[0]])
                if geo['features']:
                    c = geo['features'][0]['geometry']['coordinates']
                    st.session_state.last_coords = [c[1], c[0]]
                    st.session_state.route_data = get_route(c[1], c[0])
                else:
                    st.toast("❌ Adresse introuvable", icon="🌍")
            except:
                st.error("Erreur technique")

    st.markdown("---")

    # AFFICHAGE DU RÉSULTAT (Style Dashboard Ludique)
    if st.session_state.route_data:
        d = st.session_state.route_data
        i = d['price_info']
        
        # Injection HTML pour le Design "Carte Pro"
        st.markdown(f"""
        <div class="main-card">
            <span class="zone-pill" style="background-color: {i['color']};">{i['label']}</span>
            <div class="price-display" style="color: {i['color']};">{i['total']:.2f}€</div>
            <div style="color: #adb5bd; font-size: 0.8rem; font-weight: 500;">Total Prestation TTC</div>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <span class="stat-icon">⏱️</span>
                    <span class="stat-val">{d['duration_min']}</span>
                    <span class="stat-label">min</span>
                </div>
                <div class="stat-box">
                    <span class="stat-icon">📏</span>
                    <span class="stat-val">{d['dist_km']}</span>
                    <span class="stat-label">km</span>
                </div>
                <div class="stat-box">
                    <span class="stat-icon">⛽</span>
                    <span class="stat-val">+{i['fee']}€</span>
                    <span class="stat-label">frais</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        # Message d'accueil vide
        st.markdown("""
        <div style="text-align:center; padding: 20px; color: #aaa;">
            <div style="font-size: 3rem; margin-bottom: 10px;">🗺️</div>
            <p>Cliquez sur la carte ou entrez une adresse pour commencer.</p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# 🗺️ CARTE (Style Doux "Voyager")
# =========================================================

# Carte Pastel/Moderne
m = folium.Map(
    location=HOME_COORDS, 
    zoom_start=11, 
    tiles='https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', 
    attr='CartoDB'
)

# Zones (Couleurs distinctes mais transparentes)
iso = get_isochrones()
if iso:
    def style_zones(feature):
        v = feature['properties']['value']
        c = "#636e72"
        if v <= 10000: c = "#00b894"   # Zone 1
        elif v <= 15000: c = "#0984e3" # Zone 2
        elif v <= 20000: c = "#fdcb6e" # Zone 3
        elif v <= 25000: c = "#e056fd" # Zone 4
        elif v <= 30000: c = "#d63031" # Zone 5
        
        return { 'fillColor': c, 'color': c, 'weight': 2, 'fillOpacity': 0.1, 'opacity': 0.5, 'interactive': False }
    folium.GeoJson(iso, style_function=style_zones).add_to(m)

# Marqueur Maison
folium.Marker(HOME_COORDS, tooltip="Siège", icon=folium.Icon(color="black", icon="home", prefix="fa")).add_to(m)

# Trajet
if st.session_state.route_data:
    folium.PolyLine(st.session_state.route_data['geometry'], color="#2d3436", weight=5, opacity=0.8).add_to(m)
    folium.Marker(st.session_state.last_coords, icon=folium.Icon(color="red", icon="user", prefix="fa")).add_to(m)

# Gestion Clic
out = st_folium(m, width="100%", height=750) # Hauteur augmentée pour confort

if out['last_clicked']:
    clat, clon = out['last_clicked']['lat'], out['last_clicked']['lng']
    # Anti-rebond (éviter rechargement si même clic)
    same = False
    if st.session_state.last_coords and abs(st.session_state.last_coords[0] - clat) < 0.0001: same = True
    
    if not same:
        st.session_state.last_coords = [clat, clon]
        st.session_state.route_data = get_route(clat, clon)
        st.rerun()
