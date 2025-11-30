import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
import os

# =========================================================
# ⚙️ CONFIGURATION
# =========================================================

# Coordonnées EXACTES de votre maison (Auby)
HOME_COORDS = [50.414787, 3.056332]

# Clé API (Utilisée uniquement la première fois pour générer le fichier mémoire)
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# --- MODIFICATION ICI : Zone 1 à 1.00€ ---
ZONES_CONFIG = [
    {"dist": 30000, "price": 6.00, "color": "#d63031", "label": "Zone 5 (30km)"},
    {"dist": 25000, "price": 4.50, "color": "#e056fd", "label": "Zone 4 (25km)"},
    {"dist": 20000, "price": 3.00, "color": "#fdcb6e", "label": "Zone 3 (20km)"},
    {"dist": 15000, "price": 1.50, "color": "#0984e3", "label": "Zone 2 (15km)"},
    {"dist": 10000, "price": 1.00, "color": "#00b894", "label": "Zone 1 (10km)"}, # <--- MODIFIÉ (1€)
]

ZONE_FILE = "zones_memoire.json"

# =========================================================
# 🛠️ FONCTIONS
# =========================================================

def get_cached_isochrones():
    # Charge ou télécharge les zones UNE SEULE FOIS
    if os.path.exists(ZONE_FILE):
        try:
            with open(ZONE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass 

    try:
        headers = {'Authorization': ORS_API_KEY, 'Content-Type': 'application/json'}
        body = {
            "locations": [[HOME_COORDS[1], HOME_COORDS[0]]],
            "range": [z["dist"] for z in ZONES_CONFIG],
            "range_type": "distance", "units": "m", "smoothing": 5
        }
        r = requests.post('https://api.openrouteservice.org/v2/isochrones/driving-car', json=body, headers=headers)
        if r.status_code == 200:
            data = r.json()
            with open(ZONE_FILE, 'w') as f:
                json.dump(data, f)
            return data
    except:
        return None

def get_route_osrm(dest_lat, dest_lon):
    # Calcul itinéraire OSRM (Gratuit & Rapide)
    base_url = f"http://router.project-osrm.org/route/v1/driving/{HOME_COORDS[1]},{HOME_COORDS[0]};{dest_lon},{dest_lat}"
    
    # On force l'exclusion des péages
    params = {"overview": "full", "geometries": "geojson", "exclude": "motorway,toll"}
    
    data = None
    toll_free = True

    try:
        # Essai 1 : Sans péage
        r = requests.get(base_url, params=params, timeout=5)
        if r.status_code == 200 and r.json().get('code') == 'Ok':
            data = r.json()
        else:
            raise Exception("Fallback")
    except:
        # Essai 2 : Route standard (si destination trop loin ou bug serveur)
        toll_free = False
        try:
            r = requests.get(base_url, params={"overview": "full", "geometries": "geojson"}, timeout=5)
            if r.status_code == 200:
                data = r.json()
        except:
            pass

    if data:
        route = data['routes'][0]
        dist_km = round(route['distance'] / 1000, 1)
        duration_min = round(route['duration'] / 60)
        geometry = [(lat, lon) for lon, lat in route['geometry']['coordinates']]
        
        return {
            "dist_km": dist_km,
            "duration_min": duration_min,
            "geometry": geometry,
            "price_info": calculate_price(dist_km),
            "toll_free": toll_free
        }
    return None

def calculate_price(km):
    base = 25.00
    fee = 6.00
    label = "Hors Zone (>30km)"
    color = "#636e72"
    
    sorted_zones = sorted(ZONES_CONFIG, key=lambda x: x['dist'])
    for zone in sorted_zones:
        if km <= (zone['dist'] / 1000):
            fee = zone['price']
            color = zone['color']
            label = zone['label']
            break
            
    return {"total": base + fee, "fee": fee, "color": color, "label": label}

def search_nominatim(address):
    # User-Agent pour éviter le blocage
    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {'User-Agent': 'DelepineServicesApp/2.0 (contact@delepine.com)'}
        params = {"q": address, "format": "json", "limit": 1, "countrycodes": "fr"}
        
        r = requests.get(url, params=params, headers=headers, timeout=5)
        if r.status_code == 200 and len(r.json()) > 0:
            res = r.json()[0]
            return float(res['lat']), float(res['lon'])
    except Exception as e:
        st.error(f"Erreur recherche: {e}")
    return None

# =========================================================
# 🖥️ APPLICATION
# =========================================================
st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 400px; max-width: 400px; }
    .price-box {
        background-color: #fff; padding: 20px; border-radius: 12px;
        text-align: center; border: 1px solid #eee; border-top: 8px solid #ccc;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;
    }
    .big-price { font-size: 42px; font-weight: 800; margin: 10px 0; color: #2d3436; }
    .zone-badge {
        display: inline-block; padding: 6px 18px; border-radius: 20px;
        color: white; font-weight: bold; text-transform: uppercase; font-size: 0.9rem;
    }
    .legend-row {
        display: flex; justify-content: space-between; padding: 5px 10px;
        margin-bottom: 2px; border-radius: 4px; color: white; font-size: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'route_data' not in st.session_state: st.session_state.route_data = None
if 'last_coords' not in st.session_state: st.session_state.last_coords = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏠 Delepine Services")
    st.caption("📍 Départ : Auby")
    
    # 1. Barre de recherche
    st.markdown("---")
    c1, c2 = st.columns([3, 1])
    with c1:
        addr_input = st.text_input("Adresse", placeholder="Ville, Rue...", label_visibility="collapsed")
    with c2:
        search_clicked = st.button("🔎", type="primary")

    if search_clicked and addr_input:
        with st.spinner("Recherche..."):
            coords = search_nominatim(addr_input)
            if coords:
                st.session_state.last_coords = coords
                st.session_state.route_data = get_route_osrm(coords[0], coords[1])
                st.rerun()
            else:
                st.error("Adresse introuvable. Essayez avec le code postal.")

    # 2. Affichage des résultats
    if st.session_state.route_data:
        d = st.session_state.route_data
        p = d['price_info']
        warn_msg = "✅ Sans Péage" if d['toll_free'] else "⚠️ Route Standard"
        
        st.markdown(f"""
        <div class="price-box" style="border-top-color: {p['color']};">
            <div class="zone-badge" style="background-color: {p['color']};">{p['label']}</div>
            <div class="big-price" style="color: {p['color']};">{p['total']:.2f} €</div>
            <div style="font-size:0.9rem; color:#666; margin-bottom:10px;">
                Distance: <b>{d['dist_km']} km</b> | Durée: <b>{d['duration_min']} min</b>
            </div>
            <div style="font-size:0.75rem; background:#eee; padding:5px; border-radius:4px;">{warn_msg}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 3. Légende
    st.markdown("---")
    st.caption("Tarifs par zones")
    for z in sorted(ZONES_CONFIG, key=lambda x: x['dist']):
        p_txt = "Gratuit" if z['price'] == 0 else f"+{z['price']:.2f} €"
        st.markdown(f'<div class="legend-row" style="background:{z["color"]}"><span>Zone {int(z["dist"]/1000)} km</span><span>{p_txt}</span></div>', unsafe_allow_html=True)

# --- CARTE ---
m = folium.Map(location=HOME_COORDS, zoom_start=11, tiles='CartoDB voyager')

zones_json = get_cached_isochrones()
if zones_json:
    def style_fn(feature):
        val = feature['properties']['value']
        col = "#636e72"
        for z in sorted(ZONES_CONFIG, key=lambda x: x['dist']):
            if val <= z['dist']: col = z['color']; break
        return {'fillColor': col, 'color': col, 'weight': 1, 'fillOpacity': 0.15}
    folium.GeoJson(zones_json, style_function=style_fn, interactive=False).add_to(m)

folium.Marker(HOME_COORDS, icon=folium.Icon(color="black", icon="home", prefix="fa"), tooltip="Siège").add_to(m)

if st.session_state.route_data:
    folium.PolyLine(st.session_state.route_data['geometry'], color="#2d3436", weight=5, opacity=0.8).add_to(m)
    folium.Marker(st.session_state.last_coords, icon=folium.Icon(color="red", icon="user", prefix="fa")).add_to(m)

map_out = st_folium(m, width="100%", height=700)

if map_out['last_clicked']:
    clat = map_out['last_clicked']['lat']
    clon = map_out['last_clicked']['lng']
    
    is_new = True
    if st.session_state.last_coords:
        if abs(st.session_state.last_coords[0] - clat) < 0.0001:
            is_new = False
    
    if is_new:
        with st.spinner("Calcul itinéraire..."):
            st.session_state.last_coords = [clat, clon]
            st.session_state.route_data = get_route_osrm(clat, clon)
            st.rerun()
