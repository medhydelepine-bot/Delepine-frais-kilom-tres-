import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

# =========================================================
# 🔑 CONFIGURATION
# =========================================================

# Coordonnées EXACTES de votre maison (Auby)
HOME_COORDS = [50.414787, 3.056332]

# Configuration des Zones (Cercles concentriques)
ZONES_CONFIG = [
    {"limit": 30, "radius": 30000, "price": 6.00, "color": "#d63031", "label": "Zone 5"},
    {"limit": 25, "radius": 25000, "price": 4.50, "color": "#e056fd", "label": "Zone 4"},
    {"limit": 20, "radius": 20000, "price": 3.00, "color": "#fdcb6e", "label": "Zone 3"},
    {"limit": 15, "radius": 15000, "price": 1.50, "color": "#0984e3", "label": "Zone 2"},
    {"limit": 10, "radius": 10000, "price": 0.00, "color": "#00b894", "label": "Zone 1"},
]

# =========================================================

st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 400px; max-width: 400px; }
    
    .price-box {
        background-color: #ffffff;
        padding: 15px; border-radius: 10px; text-align: center;
        border: 1px solid #eee; border-top: 6px solid #ccc;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 15px; margin-top: 10px;
    }
    .big-price { font-size: 38px; font-weight: 800; margin: 5px 0; }
    .zone-badge {
        display: inline-block; padding: 5px 15px; border-radius: 15px;
        color: white; font-weight: bold; text-transform: uppercase;
        font-size: 0.8rem; letter-spacing: 1px; margin-bottom: 5px;
    }
    .route-type-badge {
        font-size: 0.75rem; color: #555; background: #f1f2f6;
        padding: 2px 8px; border-radius: 4px; margin-top: 5px; display: inline-block;
    }
    .info-container {
        margin-top: 10px; font-size: 0.9rem; color: #555;
        display: flex; flex-direction: column; align-items: center; gap: 6px;
    }
    .info-line {
        display: flex; justify-content: space-between; width: 85%;
        border-bottom: 1px dotted #eee; padding-bottom: 2px;
    }
    .legend-row {
        display: flex; justify-content: space-between; padding: 4px 12px;
        margin-bottom: 3px; border-radius: 4px; color: white;
        font-weight: 600; font-size: 0.8rem; align-items: center;
    }
    div[data-testid="stImage"] { display: flex; justify-content: center; }
    h1, h2, h3 { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- MEMOIRE ---
if 'route_data' not in st.session_state:
    st.session_state.route_data = None
if 'last_coords' not in st.session_state:
    st.session_state.last_coords = None

# --- CALCULS ---
def calculate_price_tier(km):
    base_price = 25.00
    fee = 6.00
    color = "#636e72"
    label = "HORS ZONE (>30km)"
    
    sorted_zones = sorted(ZONES_CONFIG, key=lambda x: x['limit'])
    
    for zone in sorted_zones:
        if km <= zone['limit']:
            fee = zone['price']
            color = zone['color']
            label = f"{zone['label']} (+{fee}€)" if fee > 0 else f"{zone['label']} (Gratuit)"
            break
            
    return { "total": base_price + fee, "fee": fee, "color": color, "label": label }

def get_route_osrm(dest_lat, dest_lon):
    # URL de base OSRM
    base_url = f"http://router.project-osrm.org/route/v1/driving/{HOME_COORDS[1]},{HOME_COORDS[0]};{dest_lon},{dest_lat}"
    
    # Configuration par défaut
    route_found = False
    data_json = None
    avoid_highways = True # On tente d'abord sans autoroute
    
    # 1. TENTATIVE : SANS AUTOROUTE (exclude=motorway,toll)
    try:
        params = {"overview": "full", "geometries": "geojson", "exclude": "motorway,toll"}
        r = requests.get(base_url, params=params, timeout=4)
        if r.status_code == 200:
            res = r.json()
            # Le serveur public renvoie parfois "NotImplemented" pour les exclusions
            if res.get('code') == 'Ok':
                data_json = res
                route_found = True
    except:
        pass # Si ça plante, on passe au plan B

    # 2. PLAN B : ROUTE STANDARD (Si l'exclusion échoue sur le serveur gratuit)
    if not route_found:
        avoid_highways = False
        try:
            params = {"overview": "full", "geometries": "geojson"} # Pas d'exclusion
            r = requests.get(base_url, params=params, timeout=4)
            if r.status_code == 200:
                res = r.json()
                if res.get('code') == 'Ok':
                    data_json = res
                    route_found = True
        except Exception as e:
            st.error(f"Erreur connexion serveur route : {e}")

    if route_found and data_json:
        route = data_json['routes'][0]
        dist_km = round(route['distance'] / 1000, 1)
        duration_min = round(route['duration'] / 60)
        geometry = route['geometry']['coordinates']
        decoded_geom = [(lat, lon) for lon, lat in geometry]
        
        return { 
            "dist_km": dist_km, 
            "duration_min": duration_min, 
            "geometry": decoded_geom, 
            "price_info": calculate_price_tier(dist_km),
            "avoid_highways": avoid_highways # Pour affichage dans l'interface
        }
    return None

def search_address_nominatim(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1, "countrycodes": "fr"}
    headers = {'User-Agent': 'DelepineApp/1.0'}
    try:
        r = requests.get(url, params=params, headers=headers)
        if r.status_code == 200 and len(r.json()) > 0:
            res = r.json()[0]
            return float(res['lat']), float(res['lon'])
    except:
        return None
    return None

# =========================================================
# 🖥️ BARRE LATERALE
# =========================================================
with st.sidebar:
    try:
        col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
        with col_logo2:
            st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h2 style='text-align: center;'>🏠 Delepine Services</h2>", unsafe_allow_html=True)

    st.caption("📍 Siège : Auby (Maison)")

    # Recherche
    st.markdown("---")
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        address_input = st.text_input("Recherche", label_visibility="collapsed", placeholder="Adresse (Ville, Rue...)")
    with col_btn:
        search_btn = st.button("🔎", type="primary")
    
    if search_btn and address_input:
        coords = search_address_nominatim(address_input)
        if coords:
            st.session_state.last_coords = [coords[0], coords[1]]
            st.session_state.route_data = get_route_osrm(coords[0], coords[1])
            st.rerun()
        else:
            st.error("Adresse introuvable")

    # Affichage Résultat
    if st.session_state.route_data:
        data = st.session_state.route_data
        info = data['price_info']
        
        # Gestion du petit label "Type de route"
        route_label = "✅ Route Secondaire (Sans Péage)" if data['avoid_highways'] else "⚠️ Route Standard (Exclusion échouée)"
        
        st.markdown(f"""
        <div class="price-box" style="border-top-color: {info['color']};">
            <div class="zone-badge" style="background-color: {info['color']};">{info['label']}</div>
            <div style="color:#999; font-size:0.75rem; margin-top:5px;">TOTAL PRESTATION</div>
            <div class="big-price" style="color: {info['color']};">{info['total']:.2f} €</div>
            <div class="info-container">
                <div class="info-line"><span>⏱️ Temps</span> <b>{data['duration_min']} min</b></div>
                <div class="info-line"><span>📏 Distance</span> <b>{data['dist_km']} km</b></div>
                <div class="info-line"><span>⛽ Supplément</span> <b>{info['fee']:.2f} €</b></div>
            </div>
            <div class="route-type-badge">{route_label}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👈 Entrez une adresse pour calculer l'itinéraire sans péage.")

    # Tableau Tarifaire
    st.markdown("---")
    st.markdown("<h5 style='text-align: center; margin-bottom: 15px;'>🏷️ Grille Tarifaire</h5>", unsafe_allow_html=True)
    st.markdown('<div style="width: 95%; margin: 0 auto;">', unsafe_allow_html=True)
    
    for zone in sorted(ZONES_CONFIG, key=lambda x: x['limit']):
        price_txt = "Gratuit" if zone['price'] == 0 else f"+{zone['price']:.2f} €"
        dist_txt = f"{zone['limit']-5}-{zone['limit']} km" if zone['limit'] > 10 else f"0-{zone['limit']} km"
        st.markdown(f"""
        <div class="legend-row" style="background:{zone['color']};">
            <span>{zone['label']} ({dist_txt})</span><span>{price_txt}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="legend-row" style="background:#636e72;">
            <span>Hors Zone (>30 km)</span><span>+6.00 €</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 🗺️ CARTE
# =========================================================
tiles_url = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
tiles_attr = '&copy; OSM contributors &copy; CARTO'

m = folium.Map(location=HOME_COORDS, zoom_start=10, tiles=tiles_url, attr=tiles_attr)

# Zones (Cercles)
for zone in ZONES_CONFIG:
    folium.Circle(
        location=HOME_COORDS,
        radius=zone['radius'],
        color=zone['color'],
        fill=True, fill_color=zone['color'], fill_opacity=0.08,
        weight=1, popup=f"{zone['label']} (+{zone['price']}€)"
    ).add_to(m)

folium.Marker(HOME_COORDS, popup="<b>Siège Delepine</b>", icon=folium.Icon(color="black", icon="home", prefix="fa")).add_to(m)

if st.session_state.route_data:
    # On change la couleur de la route si c'est "Sans autoroute" (Vert) ou "Standard" (Gris foncé)
    route_color = "#00b894" if st.session_state.route_data['avoid_highways'] else "#2d3436"
    
    folium.PolyLine(
        locations=st.session_state.route_data['geometry'], 
        color=route_color, 
        weight=4, opacity=0.8,
    ).add_to(m)
    
    folium.Marker(st.session_state.last_coords, icon=folium.Icon(color="red", icon="user", prefix="fa")).add_to(m)

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
        st.session_state.route_data = get_route_osrm(clicked_lat, clicked_lon)
        st.rerun()
