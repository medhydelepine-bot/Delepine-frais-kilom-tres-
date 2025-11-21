import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 🔑 CONFIGURATION
# =========================================================
# Collez votre clé API ci-dessous entre les guillemets
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# Coordonnées du siège (Auby)
HOME_COORDS = [50.4137, 3.0568]
# =========================================================

st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .price-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border-left: 8px solid #ccc;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .big-price {
        font-size: 40px;
        font-weight: bold;
        color: #27ae60;
        margin: 0;
    }
    .zone-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 15px;
        color: white;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.8rem;
        margin-bottom: 10px;
    }
    .info-row {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
        font-size: 0.95rem;
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

# --- ETAT ---
if 'route_data' not in st.session_state:
    st.session_state.route_data = None
if 'last_coords' not in st.session_state:
    st.session_state.last_coords = None

# --- FONCTIONS ---
def calculate_price_tier(km):
    base_price = 25.00
    fee = 0
    color = "#7f8c8d"
    label = "HORS ZONE"
    
    if km <= 10:
        fee = 0; color = "#2ecc71"; label = "Zone 1 (Gratuit)"
    elif km <= 15:
        fee = 1.50; color = "#f1c40f"; label = "Zone 2"
    elif km <= 20:
        fee = 3.00; color = "#e67e22"; label = "Zone 3"
    elif km <= 25:
        fee = 4.50; color = "#d35400"; label = "Zone 4"
    elif km <= 30:
        fee = 6.00; color = "#c0392b"; label = "Zone 5"
    else:
        fee = 6.00; color = "#7f8c8d"; label = "Hors Zone (>30km)"
        
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
        return { 
            "dist_km": dist_km, 
            "duration_min": duration_min, 
            "geometry": decoded_geom, 
            "price_info": calculate_price_tier(dist_km) 
        }
    except:
        return None

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", width=140)
    except:
        st.warning("⚠️ Image 'logo.png' manquante")

    st.title("Delepine Services")
    st.caption("📍 Siège : 21 rue Paul Bert, 59950 Auby")

    address_input = st.text_input("Recherche adresse :")
    if st.button("Rechercher 🔍") and address_input and client:
        try:
            geocode = client.pelias_search(text=address_input, focus_point=[HOME_COORDS[1], HOME_COORDS[0]])
            if geocode['features']:
                coords = geocode['features'][0]['geometry']['coordinates']
                st.session_state.last_coords = [coords[1], coords[0]]
                st.session_state.route_data = get_route(coords[1], coords[0])
            else:
                st.error("Adresse introuvable")
        except:
            st.error("Erreur Recherche")

    st.markdown("---")

    if st.session_state.route_data:
        data = st.session_state.route_data
        info = data['price_info']
        
        st.markdown(f"""
        <div class="price-box" style="border-left-color: {info['color']};">
            <div class="zone-badge" style="background-color: {info['color']};">{info['label']}</div>
            <div>Total Prestation</div>
            <div class="big-price" style="color: {info['color']};">{info['total']:.2f} €</div>
            <div style="text-align:left; margin-top:15px; color:#444;">
                <div class="info-row"><span>⏱️ Temps :</span> <b>{data['duration_min']} min</b></div>
                <div class="info-row"><span>📏 Distance :</span> <b>{data['dist_km']} km</b></div>
                <div class="info-row"><span>⛽ Supplément :</span> <b>{info['fee']:.2f} €</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👈 Entrez une adresse ou cliquez sur la carte.")

# --- CARTE ---
tiles_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'
tiles_attr = 'Tiles &copy; Esri'

m = folium.Map(location=HOME_COORDS, zoom_start=10, tiles=tiles_url, attr=tiles_attr)

# Zones
iso_data = get_isochrones()
if iso_data:
    def style_zones(feature):
        val = feature['properties']['value']
        col = "#c0392b"
        if val <= 10000: col = "#2ecc71"
        elif val <= 15000: col = "#f1c40f"
        elif val <= 20000: col = "#e67e22"
        elif val <= 25000: col = "#d35400"
        return { 'fillColor': col, 'color': col, 'weight': 1, 'fillOpacity': 0.15, 'interactive': False }
    folium.GeoJson(iso_data, style_function=style_zones).add_to(m)

# Marqueurs et Trajet (Code corrigé ici pour éviter l'erreur)
folium.Marker(
    HOME_COORDS, 
    popup="Siège Delepine", 
    icon=folium.Icon(color="black", icon="home", prefix="fa")
).add_to(m)

if st.session_state.route_data:
    folium.PolyLine(
        locations=st.session_state.route_data['geometry'], 
        color="#2c3e50", weight=6, opacity=0.9
    ).add_to(m)
    folium.Marker(
        st.session_state.last_coords, 
        icon=folium.Icon(color="blue", icon="user", prefix="fa")
    ).add_to(m)

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
