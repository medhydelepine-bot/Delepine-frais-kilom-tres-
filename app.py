import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 🔑 CONFIGURATION
# =========================================================
# Collez votre clé API entre les guillemets ci-dessous
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# Coordonnées du siège (Auby)
HOME_COORDS = [50.4137, 3.0568]
# =========================================================

st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

# --- CSS (Style visuel) ---
st.markdown("""
    <style>
    .price-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border-left: 8px solid #ccc;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .big-price {
        font-size: 45px;
        font-weight: 800;
        margin: 5px 0;
    }
    .zone-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 20px;
        color: white;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .info-row {
        display: flex;
        justify-content: space-between;
        margin-top: 12px;
        border-bottom: 1px solid #f0f0f0;
        padding-bottom: 8px;
        font-size: 0.95rem;
        color: #555;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLIENT API ---
client = None
if ORS_API_KEY and ORS_API_KEY != "VOTRE_CLE_API_ICI":
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
    except:
        st.error("Erreur de connexion API")

# --- MEMOIRE (Session State) ---
if 'route_data' not in st.session_state:
    st.session_state.route_data = None
if 'last_coords' not in st.session_state:
    st.session_state.last_coords = None

# --- CALCUL DU PRIX ET COULEURS ---
def calculate_price_tier(km):
    base_price = 25.00
    fee = 0
    # J'utilise ici les mêmes couleurs que sur la carte pour la cohérence
    color = "#7f8c8d" 
    label = "HORS ZONE"
    
    if km <= 10:
        fee = 0; color = "#00b894"; label = "Zone 1 (Gratuit)" # Vert Menthe
    elif km <= 15:
        fee = 1.50; color = "#0984e3"; label = "Zone 2 (+1.50€)" # Bleu Vif
    elif km <= 20:
        fee = 3.00; color = "#fdcb6e"; label = "Zone 3 (+3.00€)" # Jaune Moutarde
    elif km <= 25:
        fee = 4.50; color = "#e056fd"; label = "Zone 4 (+4.50€)" # Violet/Rose
    elif km <= 30:
        fee = 6.00; color = "#d63031"; label = "Zone 5 (+6.00€)" # Rouge
    else:
        fee = 6.00; color = "#636e72"; label = "Hors Zone (>30km)"
        
    return { "total": base_price + fee, "fee": fee, "color": color, "label": label }

# --- RECUPERATION DES ZONES (ISOCHRONES) ---
@st.cache_data
def get_isochrones():
    if not client: return None
    try:
        # On demande les 5 zones d'un coup
        return client.isochrones(
            locations=[[HOME_COORDS[1], HOME_COORDS[0]]],
            range=[30000, 25000, 20000, 15000, 10000],
            range_type="distance", units="m", smoothing=5
        )
    except:
        return None

# --- CALCUL ITINERAIRE ---
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
        return { 
            "dist_km": dist_km, 
            "duration_min": duration_min, 
            "geometry": decoded_geom, 
            "price_info": calculate_price_tier(dist_km) 
        }
    except:
        return None

# =========================================================
# 🖥️ BARRE LATERALE
# =========================================================
with st.sidebar:
    try:
        st.image("logo.png", width=140)
    except:
        st.warning("⚠️ Image 'logo.png' introuvable")

    st.title("Delepine Services")
    st.caption("📍 Siège : 21 rue Paul Bert, 59950 Auby")

    # Recherche
    address_input = st.text_input("Adresse client :")
    col1, col2 = st.columns([1,2])
    with col1:
        search_btn = st.button("GO 🔎")
    
    if search_btn and address_input and client:
        try:
            geocode = client.pelias_search(text=address_input, focus_point=[HOME_COORDS[1], HOME_COORDS[0]])
            if geocode['features']:
                coords = geocode['features'][0]['geometry']['coordinates']
                st.session_state.last_coords = [coords[1], coords[0]]
                st.session_state.route_data = get_route(coords[1], coords[0])
            else:
                st.error("Introuvable")
        except:
            st.error("Erreur")

    st.markdown("---")

    # Affichage du prix
    if st.session_state.route_data:
        data = st.session_state.route_data
        info = data['price_info']
        
        st.markdown(f"""
        <div class="price-box" style="border-left-color: {info['color']};">
            <div class="zone-badge" style="background-color: {info['color']};">{info['label']}</div>
            <div style="color:#999; font-size:0.8rem;">Total Prestation</div>
            <div class="big-price" style="color: {info['color']};">{info['total']:.2f} €</div>
            <div style="text-align:left; margin-top:15px;">
                <div class="info-row"><span>⏱️ Temps trajet</span> <b>{data['duration_min']} min</b></div>
                <div class="info-row"><span>📏 Distance réelle</span> <b>{data['dist_km']} km</b></div>
                <div class="info-row"><span>⛽ Supplément</span> <b>{info['fee']:.2f} €</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👈 Indiquez une adresse ou cliquez sur la carte.")

# =========================================================
# 🗺️ CARTE (COULEURS VIVES + TRANSPARENCE)
# =========================================================

# Fond de carte Esri (Rues bien visibles)
tiles_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'
tiles_attr = 'Tiles &copy; Esri'
m = folium.Map(location=HOME_COORDS, zoom_start=10, tiles=tiles_url, attr=tiles_attr)

# Affichage des Zones avec COULEURS DISTINCTES et TRANSPARENCE FORTE
iso_data = get_isochrones()
if iso_data:
    def style_zones(feature):
        val = feature['properties']['value']
        # Définition des couleurs
        col = "#636e72" # Gris par défaut
        if val <= 10000: col = "#00b894"   # Zone 1: Vert Menthe
        elif val <= 15000: col = "#0984e3" # Zone 2: Bleu
        elif val <= 20000: col = "#fdcb6e" # Zone 3: Jaune
        elif val <= 25000: col = "#e056fd" # Zone 4: Violet
        elif val <= 30000: col = "#d63031" # Zone 5: Rouge
        
        return { 
            'fillColor': col, 
            'color': col,       # Couleur de la bordure
            'weight': 2,        # Bordure un peu plus épaisse pour bien voir la limite
            'fillOpacity': 0.1, # <--- ICI : 0.1 = Très transparent (on voit bien la carte)
            'opacity': 0.8,     # La bordure reste bien visible
            'interactive': False 
        }
    folium.GeoJson(iso_data, style_function=style_zones).add_to(m)

# Marqueur Siège
folium.Marker(
    HOME_COORDS, 
    popup="Siège Delepine", 
    icon=folium.Icon(color="black", icon="home", prefix="fa")
).add_to(m)

# Trajet (Ligne noire bien contrastée)
if st.session_state.route_data:
    folium.PolyLine(
        locations=st.session_state.route_data['geometry'], 
        color="#2d3436", weight=5, opacity=1
    ).add_to(m)
    folium.Marker(
        st.session_state.last_coords, 
        icon=folium.Icon(color="blue", icon="user", prefix="fa")
    ).add_to(m)

# Gestion du clic
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
