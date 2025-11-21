import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 🔑 CONFIGURATION - À REMPLIR OBLIGATOIREMENT
# =========================================================
# Collez votre clé API OpenRouteService ici
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# Coordonnées du siège (Auby)
HOME_COORDS = [50.414787, 3.056332]
# =========================================================

# Configuration de la page
st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

# --- CSS PERSONNALISÉ (Pour le look) ---
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

# Initialisation du client API
client = None
if ORS_API_KEY and ORS_API_KEY != "VOTRE_CLE_API_ICI":
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
    except:
        st.error("Erreur de connexion API")

# --- GESTION DE L'ÉTAT ---
if 'route_data' not in st.session_state:
    st.session_state.route_data = None
if 'last_coords' not in st.session_state:
    st.session_state.last_coords = None

# --- FONCTION CALCUL PRIX ---
def calculate_price_tier(km):
    base_price = 25.00
    fee = 0
    color = "#7f8c8d"
    label = "HORS ZONE"
    
    if km <= 10:
        fee = 0
        color = "#2ecc71"
        label = "Zone 1 (Gratuit)"
    elif km <= 15:
        fee = 1.50
        color = "#f1c40f"
        label = "Zone 2"
    elif km <= 20:
        fee = 3.00
        color = "#e67e22"
        label = "Zone 3"
    elif km <= 25:
        fee = 4.50
        color = "#d35400"
        label = "Zone 4"
    elif km <= 30:
        fee = 6.00
        color = "#c0392b"
        label = "Zone 5"
    else:
        fee = 6.00 
        color = "#7f8c8d"
        label = "Hors Zone (>30km)"
        
    return { "total": base_price + fee, "fee": fee, "color": color, "label": label }

# --- FONCTION CACHÉE POUR LES ZONES (ISOCHRONES) ---
@st.cache_data
def get_isochrones():
    if not client: return None
    try:
        # Note: l'API prend [lon, lat]
        iso = client.isochrones(
            locations=[[HOME_COORDS[1], HOME_COORDS[0]]],
            range=[30000, 25000, 20000, 15000, 10000],
            interval=5000,
            range_type="distance",
            units="m",
            smoothing=5
        )
        return iso
    except:
        return None

# --- FONCTION ITINÉRAIRE ---
def get_route(dest_lat, dest_lon):
    if not client: return None
    try:
        coords = [[HOME_COORDS[1], HOME_COORDS[0]], [dest_lon, dest_lat]]
        routes = client.directions(coordinates=coords, profile='driving-car', format='geojson')
        summary = routes['features'][0]['properties']['summary']
        dist_km = round(summary['distance'] / 1000, 1)
        duration_min = round(summary['duration'] / 60)
        geometry = routes['features'][0]['geometry']['coordinates']
        decoded_geom = [(lat, lon) for lon, lat in geometry] # Inversion pour Folium
        
        return {
            "dist_km": dist_km,
            "duration_min": duration_min,
            "geometry": decoded_geom,
            "price_info": calculate_price_tier(dist_km)
        }
    except:
        return None

# =========================================================
# 🖥️ INTERFACE (SIDEBAR)
# =========================================================
with st.sidebar:
    try:
        st.image("logo.png", width=140)
    except:
        st.warning("⚠️ Image 'logo.png' manquante")

    st.title("Delepine Services")
    st.caption("📍 Siège : 21 rue Paul Bert, 59950 Auby")

    # Recherche
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
            st.error("Erreur API")

    st.markdown("---")

    # RESULTATS
    if st.session_state.route_data:
        data = st.session_state.route_data
        info = data['price_info']
        
        html_card = f"""
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
        """
        st.markdown(html_card, unsafe_allow_html=True)
    else:
        st.info("👈 Entrez une adresse ou cliquez sur la carte.")

# =========================================================
# 🗺️ CARTE (Maintenant avec style "Vif/Ludique")
# =========================================================

# ICI : On utilise les tuiles 'Esri WorldStreetMap' pour avoir le look coloré
attr = 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'

m = folium.Map(location=HOME_COORDS, zoom_start=10, tiles=tiles, attr=attr)

# 1. Ajout des Zones
iso_data = get_isochrones()
if iso_data:
    def style_function(feature):
        val = feature['properties']['value']
        col = "#c0392b"
        if val <= 10000: col = "#2ecc71"
        elif val <= 15000: col = "#f1c40f"
        elif val <= 20000: col = "#e67e22"
        elif val <= 25000: col = "#d35400"
        return { 'fillColor': col, 'color': col, 'weight': 1, 'fillOpacity': 0.15, 'interactive': False }
    
    folium.GeoJson(iso_data, style_function=style_function).add_to(m)

# 2. Marqueur Domicile
folium.Marker(
    HOME_COORDS, 
    popup="
