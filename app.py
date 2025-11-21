import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 1. CONFIGURATION (Vos paramètres)
# =========================================================
# Votre clé API
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# Vos coordonnées (Auby)
HOME_COORDS = [50.414771, 3.056326]

# Configuration Page
st.set_page_config(page_title="Delepine Domicile", page_icon="🏡", layout="wide")

# =========================================================
# 2. DESIGN "LUDIQUE & CLAIR" (CSS)
# =========================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
        color: #333; /* Texte gris foncé, jamais noir pur */
    }

    /* FORCER LE FOND BLANC (Pour éviter le mode sombre moche) */
    .stApp {
        background-color: white;
    }
    
    [data-testid="stSidebar"] {
        background-color: #f4f6f9; /* Gris très doux pour le menu */
        border-right: 1px solid #e0e0e0;
    }

    /* BOUTONS : Gros et colorés */
    div.stButton > button {
        background-color: #2c3e50;
        color: white;
        border-radius: 12px;
        padding: 15px 0;
        font-weight: 600;
        border: none;
        width: 100%;
        box-shadow: 0 4px 0 rgba(0,0,0,0.1); /* Petit effet 3D */
        transition: transform 0.1s;
    }
    div.stButton > button:hover {
        background-color: #34495e;
        transform: translateY(-2px);
    }
    div.stButton > button:active {
        transform: translateY(2px);
        box-shadow: none;
    }

    /* CHAMP RECHERCHE (Toujours blanc) */
    div[data-baseweb="input"] {
        background-color: white !important;
        border-radius: 12px !important;
        border: 2px solid #ddd !important;
        color: black !important;
    }

    /* LA CARTE DE RÉSULTAT COLORÉE */
    .result-card {
        background: white;
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        margin-top: 20px;
        border: 2px solid transparent; /* Prêt pour la couleur */
        animation: popIn 0.3s ease-out;
    }
    
    @keyframes popIn {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }

    .zone-pill {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 50px;
        color: white;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.9rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }

    .price-big {
        font-size: 3.5rem;
        font-weight: 800;
        margin: 15px 0;
        line-height: 1;
    }

    .details-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-top: 20px;
        text-align: left;
    }
    
    .detail-item {
        background: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLIENT API ---
client = None
if ORS_API_KEY:
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
    except: pass

# --- MEMOIRE ---
if 'route_data' not in st.session_state: st.session_state.route_data = None
if 'last_coords' not in st.session_state: st.session_state.last_coords = None

# --- LOGIQUE COULEURS & PRIX ---
def calculate_price_tier(km):
    base_price = 25.00
    fee = 0
    
    # VOS COULEURS ZONES (Vives et Ludiques)
    if km <= 10:   
        fee = 0;    color = "#00b894"; label = "Zone 1" # Vert
    elif km <= 15: 
        fee = 1.50; color = "#0984e3"; label = "Zone 2" # Bleu
    elif km <= 20: 
        fee = 3.00; color = "#fdcb6e"; label = "Zone 3" # Jaune
    elif km <= 25: 
        fee = 4.50; color = "#e056fd"; label = "Zone 4" # Violet
    elif km <= 30: 
        fee = 6.00; color = "#d63031"; label = "Zone 5" # Rouge
    else:          
        fee = 6.00; color = "#636e72"; label = "Hors Zone" # Gris
        
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
# 3. INTERFACE (SIDEBAR)
# =========================================================
with st.sidebar:
    # Logo
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        try: st.image("logo.png", use_container_width=True)
        except: st.markdown("<h1>🏡</h1>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align:center; margin-top:0;'>Delepine</h3>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:#888; margin-bottom:20px;'>Domicile Services • Auby</div>", unsafe_allow_html=True)

    # Recherche simple
    st.markdown("**Nouvelle recherche :**")
    addr = st.text_input("Adresse", placeholder="Ex: Mairie de Douai...", label_visibility="collapsed")
    if st.button("GO 🚀") and addr and client:
        try:
            geo = client.pelias_search(text=addr, focus_point=[HOME_COORDS[1], HOME_COORDS[0]])
            if geo['features']:
                c = geo['features'][0]['geometry']['coordinates']
                st.session_state.last_coords = [c[1], c[0]]
                st.session_state.route_data = get_route(c[1], c[0])
            else:
                st.error("Adresse introuvable")
        except: st.error("Erreur API")

    st.markdown("---")

    # LE RÉSUMÉ COLORÉ (C'est ici qu'on utilise les couleurs de zones)
    if st.session_state.route_data:
        d = st.session_state.route_data
        i = d['price_info']
        c = i['color'] # La couleur de la zone
        
        # Carte HTML dynamique
        st.markdown(f"""
        <div class="result-card" style="border-color: {c};">
            <div class="zone-pill" style="background-color: {c};">{i['label']}</div>
            
            <div class="price-big" style="color: {c};">{i['total']:.2f} €</div>
            <div style="color: #999; font-size: 0.8rem; font-weight: 500;">TOTAL TTC</div>
            
            <div class="details-grid">
                <div class="detail-item">
                    <div style="color:#888; font-size:0.8rem;">TEMPS</div>
                    <div style="font-weight:bold; font-size:1.1rem;">{d['duration_min']} min</div>
                </div>
                <div class="detail-item">
                    <div style="color:#888; font-size:0.8rem;">DISTANCE</div>
                    <div style="font-weight:bold; font-size:1.1rem;">{d['dist_km']} km</div>
                </div>
                <div class="detail-item">
                    <div style="color:#888; font-size:0.8rem;">FRAIS KM</div>
                    <div style="font-weight:bold; color:{c};">+{i['fee']} €</div>
                </div>
                <div class="detail-item">
                    <div style="color:#888; font-size:0.8rem;">FORFAIT</div>
                    <div style="font-weight:bold;">25.00 €</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👈 Cliquez sur la carte ou entrez une adresse.")

# =========================================================
# 4. CARTE (Style Doux + Zones Colorées)
# =========================================================

m = folium.Map(
    location=HOME_COORDS, 
    zoom_start=11, 
    tiles='https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', 
    attr='CartoDB'
)

# Zones (Couleurs vives + Transparence)
iso = get_isochrones()
if iso:
    def style_zones(feature):
        v = feature['properties']['value']
        c = "#636e72"
        # MÊMES COULEURS QUE LE RÉSUMÉ
        if v <= 10000: c = "#00b894"   # Zone 1
        elif v <= 15000: c = "#0984e3" # Zone 2
        elif v <= 20000: c = "#fdcb6e" # Zone 3
        elif v <= 25000: c = "#e056fd" # Zone 4
        elif v <= 30000: c = "#d63031" # Zone 5
        
        return { 'fillColor': c, 'color': c, 'weight': 2, 'fillOpacity': 0.15, 'opacity': 0.6, 'interactive': False }
    folium.GeoJson(iso, style_function=style_zones).add_to(m)

# Maison
folium.Marker(HOME_COORDS, tooltip="Siège", icon=folium.Icon(color="black", icon="home", prefix="fa")).add_to(m)

# Trajet
if st.session_state.route_data:
    # Ligne de trajet prenant la couleur de la zone pour être raccord !
    route_color = st.session_state.route_data['price_info']['color']
    
    folium.PolyLine(
        st.session_state.route_data['geometry'], 
        color=route_color, 
        weight=6, 
        opacity=0.9
    ).add_to(m)
    
    folium.Marker(
        st.session_state.last_coords, 
        icon=folium.Icon(color="red", icon="user", prefix="fa")
    ).add_to(m)

# Rendu
out = st_folium(m, width="100%", height=800)

if out['last_clicked']:
    clat, clon = out['last_clicked']['lat'], out['last_clicked']['lng']
    same = False
    if st.session_state.last_coords and abs(st.session_state.last_coords[0] - clat) < 0.0001: same = True
    
    if not same:
        st.session_state.last_coords = [clat, clon]
        st.session_state.route_data = get_route(clat, clon)
        st.rerun()
