import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 🔑 CONFIGURATION
# =========================================================
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# Coordonnées EXACTES de votre maison (Auby)
HOME_COORDS = [50.414787, 3.056332]
# =========================================================

st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

# --- CSS (Design Compact & Centré) ---
st.markdown("""
    <style>
    /* 1. LARGEUR & ESPACEMENT DU BANDEAU GAUCHE */
    [data-testid="stSidebar"] {
        min-width: 400px; /* Largeur confortable */
        max-width: 400px;
    }
    
    /* Réduire l'espace vertical entre les éléments du sidebar */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.5rem; 
        padding-top: 1rem;
    }

    /* 2. DESIGN DE LA BOITE DE PRIX (Plus compacte et centrée) */
    .price-box {
        background-color: #ffffff;
        padding: 15px; /* Moins de padding */
        border-radius: 10px;
        text-align: center; /* Tout centrer */
        border: 1px solid #eee;
        border-top: 6px solid #ccc; /* Bordure en haut pour gagner de la place latérale */
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 10px;
    }
    .big-price {
        font-size: 32px; /* Police réduite */
        font-weight: 800;
        margin: 5px 0;
    }
    .zone-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 15px;
        color: white;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    
    /* Lignes d'infos centrées */
    .info-container {
        margin-top: 10px;
        font-size: 0.85rem;
        color: #555;
        display: flex;
        flex-direction: column;
        align-items: center; /* Centre les éléments flex */
        gap: 5px;
    }
    .info-line {
        display: flex;
        justify-content: space-between;
        width: 80%; /* Ne prend pas toute la largeur pour rester centré visuellement */
        border-bottom: 1px dotted #eee;
    }

    /* 3. TABLEAU LÉGENDE (Compact) */
    .legend-row {
        display: flex;
        justify-content: space-between;
        padding: 4px 12px; /* Plus fin */
        margin-bottom: 3px;
        border-radius: 4px;
        color: white;
        font-weight: 600;
        font-size: 0.75rem; /* Police plus petite */
        align-items: center;
    }
    
    /* Centrage global des titres et images */
    .css-1v0mbdj.e115fcil1 {
        display: flex;
        justify-content: center;
    }
    div[data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    h1, h2, h3 {
        text-align: center;
    }
    .stCaption {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONNEXION API ---
client = None
if ORS_API_KEY:
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
    except:
        st.error("Erreur API")

# --- MEMOIRE ---
if 'route_data' not in st.session_state:
    st.session_state.route_data = None
if 'last_coords' not in st.session_state:
    st.session_state.last_coords = None

# --- CALCULS ---
def calculate_price_tier(km):
    base_price = 25.00
    fee = 0
    color = "#7f8c8d" 
    label = "HORS ZONE"
    
    if km <= 10:
        fee = 0; color = "#00b894"; label = "Zone 1 (Gratuit)"
    elif km <= 15:
        fee = 1.50; color = "#0984e3"; label = "Zone 2 (+1.50€)"
    elif km <= 20:
        fee = 3.00; color = "#fdcb6e"; label = "Zone 3 (+3.00€)"
    elif km <= 25:
        fee = 4.50; color = "#e056fd"; label = "Zone 4 (+4.50€)"
    elif km <= 30:
        fee = 6.00; color = "#d63031"; label = "Zone 5 (+6.00€)"
    else:
        fee = 6.00; color = "#636e72"; label = "Hors Zone (>30km)"
        
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
    except:
        return None

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
    except:
        return None

# =========================================================
# 🖥️ BARRE LATERALE (Design Centré)
# =========================================================
with st.sidebar:
    # 1. Logo et Titre Centrés
    try:
        col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
        with col_logo2:
            st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h2 style='text-align: center;'>🏠 Delepine Services</h2>", unsafe_allow_html=True)

    st.caption("📍 Siège : Auby (Maison)")

    # 2. Recherche Compacte
    st.markdown("---")
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        address_input = st.text_input("Adresse client :", label_visibility="collapsed", placeholder="Entrez une adresse...")
    with col_btn:
        search_btn = st.button("🔎")
    
    if search_btn and address_input and client:
        try:
            geocode = client.pelias_search(text=address_input, focus_point=[HOME_COORDS[1], HOME_COORDS[0]])
            if geocode['features']:
                coords = geocode['features'][0]['geometry']['coordinates']
                st.session_state.last_coords = [coords[1], coords[0]]
                st.session_state.route_data = get_route(coords[1], coords[0])
            else:
                st.error("Non trouvé")
        except:
            st.error("Erreur")

    # 3. Résultat Centré
    if st.session_state.route_data:
        data = st.session_state.route_data
        info = data['price_info']
        
        st.markdown(f"""
        <div class="price-box" style="border-top-color: {info['color']};">
            <div class="zone-badge" style="background-color: {info['color']};">{info['label']}</div>
            <div style="color:#999; font-size:0.7rem;">Total Prestation</div>
            <div class="big-price" style="color: {info['color']};">{info['total']:.2f} €</div>
            
            <div class="info-container">
                <div class="info-line"><span>⏱️ Temps</span> <b>{data['duration_min']} min</b></div>
                <div class="info-line"><span>📏 Distance</span> <b>{data['dist_km']} km</b></div>
                <div class="info-line"><span>⛽ Supplément</span> <b>{info['fee']:.2f} €</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👈 Indiquez une adresse")

    # 4. Tableau Compact
    st.markdown("---")
    st.markdown("<h5 style='text-align: center; margin-bottom: 10px;'>🏷️ Grille Tarifaire</h5>", unsafe_allow_html=True)
    st.markdown("""
    <div style="width: 90%; margin: 0 auto;">
        <div class="legend-row" style="background:#00b894;"><span>Zone 1 (0-10 km)</span><span>Gratuit</span></div>
        <div class="legend-row" style="background:#0984e3;"><span>Zone 2 (10-15 km)</span><span>+1.50 €</span></div>
        <div class="legend-row" style="background:#fdcb6e;"><span>Zone 3 (15-20 km)</span><span>+3.00 €</span></div>
        <div class="legend-row" style="background:#e056fd;"><span>Zone 4 (20-25 km)</span><span>+4.50 €</span></div>
        <div class="legend-row" style="background:#d63031;"><span>Zone 5 (25-30 km)</span><span>+6.00 €</span></div>
        <div class="legend-row" style="background:#636e72;"><span>Hors Zone (>30 km)</span><span>+6.00 €</span></div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 🗺️ CARTE
# =========================================================
tiles_url = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
tiles_attr = '&copy; OSM contributors &copy; CARTO'

m = folium.Map(location=HOME_COORDS, zoom_start=11, tiles=tiles_url, attr=tiles_attr)

iso_data = get_isochrones()
if iso_data:
    def style_zones(feature):
        val = feature['properties']['value']
        col = "#636e72"
        if val <= 10000: col = "#00b894"
        elif val <= 15000: col = "#0984e3"
        elif val <= 20000: col = "#fdcb6e"
        elif val <= 25000: col = "#e056fd"
        elif val <= 30000: col = "#d63031"
        
        return { 'fillColor': col, 'color': col, 'weight': 2, 'fillOpacity': 0.1, 'opacity': 0.6, 'interactive': False }
    folium.GeoJson(iso_data, style_function=style_zones).add_to(m)

folium.Marker(HOME_COORDS, popup="Siège", icon=folium.Icon(color="black", icon="home", prefix="fa")).add_to(m)

if st.session_state.route_data:
    folium.PolyLine(locations=st.session_state.route_data['geometry'], color="#2d3436", weight=5, opacity=0.8).add_to(m)
    folium.Marker(st.session_state.last_coords, icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)

map_output = st_folium(m, width="100%", height=700)

if map_output['last_clicked']:
    clicked_lat = map_output['last_clicked']['lat']
    clicked_lon = map_output['last_clicked']['lng']
    
    is_new = False
    if st.session_state.last_coords is None:
        is_new = True
    elif abs(st.session_state.last_coords[0] - clicked_lat) > 0.0001:
        is_new = True
        
    if is_new:
        st.session_state.last_coords = [clicked_lat, clicked_lon]
        st.session_state.route_data = get_route(clicked_lat, clicked_lon)
        st.rerun()
