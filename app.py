import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 🔑 CONFIGURATION
# =========================================================
# ⚠️ COLLEZ VOTRE VRAIE CLÉ API CI-DESSOUS (celle qui commence par 5b...)
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# Coordonnées EXACTES (Maison)
HOME_COORDS = [50.414771, 3.056326]
# =========================================================

st.set_page_config(page_title="Delepine Domicile", page_icon="🏡", layout="wide")

# =========================================================
# 🎨 DESIGN & CSS (Harmonisation Bleu & Homogène)
# =========================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: #37474f;
    }

    /* 1. SIDEBAR : Fond Bleu Clair */
    [data-testid="stSidebar"] {
        background-color: #e3f2fd; /* Bleu très pâle */
        border-right: 1px solid #bbdefb;
    }

    /* 2. BOUTONS : Style Homogène Bleu Pro */
    div.stButton > button {
        width: 100%;
        background-color: #1976d2; /* Bleu Standard Material */
        color: white;
        border-radius: 8px;
        padding: 12px 0;
        font-weight: 500;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: all 0.2s;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div.stButton > button:hover {
        background-color: #1565c0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-1px);
    }

    /* 3. CHAMPS DE TEXTE : Propres et blancs */
    div[data-baseweb="input"] {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #90caf9;
    }

    /* 4. RESULTATS : Carte Blanche Épurée */
    .main-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(25, 118, 210, 0.08); /* Ombre bleutée légère */
        margin-bottom: 20px;
        border: 1px solid #e1f5fe;
    }

    /* Prix */
    .price-display {
        font-size: 3rem;
        font-weight: 700;
        color: #1976d2; /* Même bleu que les boutons */
        margin: 5px 0;
    }

    /* Badges Zones uniformisés */
    .zone-pill {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 4px;
        background-color: #eceff1;
        color: #455a64;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    /* Grille stats */
    .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 8px;
        margin-top: 20px;
    }

    .stat-box {
        background: #f1f8e9; /* Fond très léger pour les stats */
        padding: 10px 5px;
        border-radius: 8px;
        color: #37474f;
    }
    
    .stat-icon { font-size: 1.2rem; display:block; margin-bottom:4px; }
    .stat-val { font-weight: 700; font-size: 0.9rem; display:block; }
    .stat-label { font-size: 0.65rem; text-transform: uppercase; opacity: 0.7; }
    
    </style>
    """, unsafe_allow_html=True)

# --- CLIENT API ---
client = None
if ORS_API_KEY:
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
    except:
        pass

# --- ETAT ---
if 'route_data' not in st.session_state: st.session_state.route_data = None
if 'last_coords' not in st.session_state: st.session_state.last_coords = None

# --- LOGIQUE ---
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
# 📱 INTERFACE SIDEBAR (Bleu Clair & Homogène)
# =========================================================
with st.sidebar:
    # En-tête
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.markdown("<h1 style='text-align:center;'>🏠</h1>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align: center; color: #1565c0; margin:0;'>Delepine Services</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #546e7a; font-size: 0.8rem; margin-bottom: 20px;'>📍 Base : Auby</p>", unsafe_allow_html=True)

    # Recherche
    with st.container():
        addr = st.text_input("Nouvelle recherche", placeholder="Ex: Mairie de Douai")
        if st.button("CALCULER") and addr and client:
            try:
                geo = client.pelias_search(text=addr, focus_point=[HOME_COORDS[1], HOME_COORDS[0]])
                if geo['features']:
                    c = geo['features'][0]['geometry']['coordinates']
                    st.session_state.last_coords = [c[1], c[0]]
                    st.session_state.route_data = get_route(c[1], c[0])
                else:
                    st.toast("Adresse introuvable", icon="❌")
            except:
                st.error("Erreur API")

    st.markdown("---")

    # RESULTATS (Style Unifié)
    if st.session_state.route_data:
        d = st.session_state.route_data
        i = d['price_info']
        
        st.markdown(f"""
        <div class="main-card">
            <span class="zone-pill">{i['label']}</span>
            <div class="price-display">{i['total']:.2f}€</div>
            <div style="color: #78909c; font-size: 0.8rem;">TOTAL PRESTATION</div>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <span class="stat-icon" style="color:#1976d2">⏱️</span>
                    <span class="stat-val">{d['duration_min']}</span>
                    <span class="stat-label">min</span>
                </div>
                <div class="stat-box">
                    <span class="stat-icon" style="color:#1976d2">📏</span>
                    <span class="stat-val">{d['dist_km']}</span>
                    <span class="stat-label">km</span>
                </div>
                <div class="stat-box">
                    <span class="stat-icon" style="color:#1976d2">⛽</span>
                    <span class="stat-val">+{i['fee']}€</span>
                    <span class="stat-label">frais</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.markdown("""
        <div style="text-align:center; padding: 20px; color: #607d8b; opacity: 0.7;">
            <div style="font-size: 2rem; margin-bottom: 10px;">🗺️</div>
            <p style="font-size: 0.9rem;">En attente d'une adresse...</p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# 🗺️ CARTE (Toujours le style "Voyager" Doux)
# =========================================================

m = folium.Map(
    location=HOME_COORDS, 
    zoom_start=11, 
    tiles='https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', 
    attr='CartoDB'
)

# Zones (Couleurs distinctes pour la carte, transparence légère)
iso = get_isochrones()
if iso:
    def style_zones(feature):
        v = feature['properties']['value']
        c = "#636e72"
        if v <= 10000: c = "#00b894"   # Vert
        elif v <= 15000: c = "#0984e3" # Bleu
        elif v <= 20000: c = "#fdcb6e" # Jaune
        elif v <= 25000: c = "#e056fd" # Violet
        elif v <= 30000: c = "#d63031" # Rouge
        
        return { 'fillColor': c, 'color': c, 'weight': 2, 'fillOpacity': 0.1, 'opacity': 0.5, 'interactive': False }
    folium.GeoJson(iso, style_function=style_zones).add_to(m)

folium.Marker(HOME_COORDS, tooltip="Siège", icon=folium.Icon(color="black", icon="home", prefix="fa")).add_to(m)

if st.session_state.route_data:
    folium.PolyLine(st.session_state.route_data['geometry'], color="#263238", weight=5, opacity=0.8).add_to(m)
    folium.Marker(st.session_state.last_coords, icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)

out = st_folium(m, width="100%", height=750)

if out['last_clicked']:
    clat, clon = out['last_clicked']['lat'], out['last_clicked']['lng']
    same = False
    if st.session_state.last_coords and abs(st.session_state.last_coords[0] - clat) < 0.0001: same = True
    
    if not same:
        st.session_state.last_coords = [clat, clon]
        st.session_state.route_data = get_route(clat, clon)
        st.rerun()
