import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 🔑 CONFIGURATION
# =========================================================
# ⚠️ REMPLACEZ PAR VOTRE VRAIE CLÉ API (Commence par 5b3...) ⚠️
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0=" 

# Coordonnées EXACTES de votre maison (Auby)
HOME_COORDS = [50.414787, 3.056332]

# =========================================================

st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

# --- CSS (Design Global) ---
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem; /* Un peu moins d'espace en haut */
    }
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

# --- CONNEXION API ---
client = None
if ORS_API_KEY and ORS_API_KEY != "VOTRE_CLE_API_ICI" and not ORS_API_KEY.startswith("eyJ"):
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
    except Exception as e:
        st.error(f"Erreur de connexion API : {e}")
elif ORS_API_KEY.startswith("eyJ"):
     st.error("⚠️ Format de clé API incorrect. Utilisez la clé standard (commençant par '5b3...')")


# --- MEMOIRE DU PROGRAMME ---
if 'route_data' not in st.session_state:
    st.session_state.route_data = None
if 'last_coords' not in st.session_state:
    st.session_state.last_coords = None

# --- FONCTIONS DE CALCUL ---
def calculate_price_tier(km):
    base_price = 25.00
    fee = 0
    color = "#7f8c8d" 
    label = "HORS ZONE"
    
    # Couleurs des badges (DOIVENT MATCHER LA LÉGENDE)
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
    except Exception as e:
        # st.warning(f"Isochrones indisponibles: {e}")
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
    except Exception as e:
        st.error(f"Erreur lors du calcul d'itinéraire : {e}")
        return None

# =========================================================
# 🖥️ BARRE LATERALE
# =========================================================
with st.sidebar:
    try:
        st.image("logo.png", width=140)
    except:
        st.markdown("## 🏠 Delepine Services")

    st.caption("📍 Siège : Auby (Maison)")

    # Champ de recherche
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
                st.rerun()
            else:
                st.error("Adresse introuvable")
        except Exception as e:
            st.error(f"Erreur de recherche: {e}")

    st.markdown("---")

    # Affichage Résultats
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
        st.info("👈 Entrez une adresse ou cliquez sur la carte.")

# =========================================================
# 🗺️ CARTE (Style "Voyager") & LÉGENDE
# =========================================================

# --- DÉFINITION DE LA LÉGENDE HTML/CSS ---
LEGEND_HTML = """
<style>
    /* Conteneur qui se superpose à la carte */
    .map-overlay-container {
        position: relative;
        width: 100%;
        height: 0; /* Astuce pour ne pas prendre de place dans le flux */
        top: -10px; /* Remonte légèrement pour coller au bas de la carte */
        z-index: 9999; /* S'assure d'être au-dessus */
        pointer-events: none; /* Laisse passer les clics sauf sur la légende elle-même */
    }
    /* La boîte de légende elle-même */
    .legend-box {
        position: absolute;
        bottom: 30px;    /* Position depuis le bas */
        left: 30px;      /* Position depuis la gauche */
        background-color: rgba(255, 255, 255, 0.90); /* Fond blanc semi-transparent */
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        font-family: sans-serif;
        pointer-events: auto; /* Réactive les clics sur la légende */
        user-select: none;
        backdrop-filter: blur(5px); /* Effet de flou d'arrière-plan moderne */
        border: 1px solid rgba(0,0,0,0.05);
    }
    .legend-box h4 {
        margin: 0 0 12px 0;
        font-size: 0.95rem;
        color: #2d3436;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #555;
    }
    /* Les petits carrés de couleur */
    .color-swatch {
        width: 18px;
        height: 18px;
        margin-right: 10px;
        border-radius: 4px;
        box-shadow: inset 0 0 0 1px rgba(0,0,0,0.1); /* Légère bordure interne */
    }
</style>

<div class="map-overlay-container">
    <div class="legend-box">
        <h4>Zones & Suppléments</h4>
        <div class="legend-item"><div class="color-swatch" style="background:#00b894;"></div>Zone 1 (Gratuit)</div>
        <div class="legend-item"><div class="color-swatch" style="background:#0984e3;"></div>Zone 2 (+1.50€)</div>
        <div class="legend-item"><div class="color-swatch" style="background:#fdcb6e;"></div>Zone 3 (+3.00€)</div>
        <div class="legend-item"><div class="color-swatch" style="background:#e056fd;"></div>Zone 4 (+4.50€)</div>
        <div class="legend-item"><div class="color-swatch" style="background:#d63031;"></div>Zone 5 (+6.00€)</div>
        <div class="legend-item"><div class="color-swatch" style="background:#636e72;"></div>Hors Zone</div>
    </div>
</div>
"""

# --- CRÉATION DE LA CARTE ---
tiles_url = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
tiles_attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

m = folium.Map(location=HOME_COORDS, zoom_start=11, tiles=tiles_url, attr=tiles_attr)

# Affichage des Zones
iso_data = get_isochrones()
if iso_data:
    def style_zones(feature):
        val = feature['properties']['value']
        col = "#636e72"
        if val <= 10000: col = "#00b894"   # Vert
        elif val <= 15000: col = "#0984e3" # Bleu
        elif val <= 20000: col = "#fdcb6e" # Jaune
        elif val <= 25000: col = "#e056fd" # Violet
        elif val <= 30000: col = "#d63031" # Rouge
        
        return { 
            'fillColor': col, 
            'color': col, 
            'weight': 1, # Bordure plus fine
            'fillOpacity': 0.15, # Un peu plus opaque pour mieux voir les couleurs
            'opacity': 0.4,
            'interactive': False 
        }
    folium.GeoJson(iso_data, style_function=style_zones).add_to(m)

# Marqueur Maison
folium.Marker(
    HOME_COORDS, 
    popup="Siège Delepine", 
    icon=folium.Icon(color="black", icon="home", prefix="fa")
).add_to(m)

# Trajet
if st.session_state.route_data:
    folium.PolyLine(
        locations=st.session_state.route_data['geometry'], 
        color="#2d3436", weight=5, opacity=0.8
    ).add_to(m)
    folium.Marker(
        st.session_state.last_coords, 
        icon=folium.Icon(color="blue", icon="user", prefix="fa")
    ).add_to(m)

# --- AFFICHAGE CARTE ET LÉGENDE ---

# 1. La carte
map_output = st_folium(m, width="100%", height=700)

# 2. La légende (injectée juste après pour se superposer)
st.markdown(LEGEND_HTML, unsafe_allow_html=True)

# --- INTERACTIVITÉ CLIC ---
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
