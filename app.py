import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

# =========================================================
# ⚙️ CONFIGURATION INTELLIGENTE
# =========================================================

# Coordonnées EXACTES de votre maison (Auby)
HOME_COORDS = [50.414787, 3.056332]

# FACTEUR DE DÉTOUR (Astuce Pro)
# 1.30 signifie qu'il faut rouler 13km pour s'éloigner de 10km à vol d'oiseau.
# Cela permet d'avoir des cercles visuels qui correspondent à la réalité de la route.
DETOUR_COEFF = 1.30 

# Configuration des Zones
# 'limit': La limite réelle payée (Route)
# 'radius': Le cercle affiché (Vol d'oiseau ajusté pour correspondre à la route)
ZONES_CONFIG = [
    {"limit": 30, "price": 6.00, "color": "#d63031", "label": "Zone 5"},
    {"limit": 25, "price": 4.50, "color": "#e056fd", "label": "Zone 4"},
    {"limit": 20, "price": 3.00, "color": "#fdcb6e", "label": "Zone 3"},
    {"limit": 15, "price": 1.50, "color": "#0984e3", "label": "Zone 2"},
    {"limit": 10, "price": 0.00, "color": "#00b894", "label": "Zone 1"},
]

# Calcul automatique des rayons visuels
for zone in ZONES_CONFIG:
    zone['radius'] = (zone['limit'] / DETOUR_COEFF) * 1000  # Conversion en mètres

# =========================================================

st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

# --- CSS PRO ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 400px; max-width: 400px; }
    
    .price-box {
        background-color: #ffffff;
        padding: 20px; border-radius: 12px; text-align: center;
        border: 1px solid #eee; border-top: 8px solid #ccc;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .big-price { font-size: 42px; font-weight: 800; margin: 10px 0; letter-spacing: -1px;}
    .zone-badge {
        display: inline-block; padding: 6px 18px; border-radius: 20px;
        color: white; font-weight: bold; text-transform: uppercase;
        font-size: 0.9rem; letter-spacing: 1px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .route-warning {
        font-size: 0.75rem; color: #fff; background: #2ecc71;
        padding: 4px 12px; border-radius: 4px; margin-top: 10px; display: inline-block;
        font-weight: 600;
    }
    .info-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
        margin-top: 15px; text-align: left;
    }
    .info-item {
        background: #f8f9fa; padding: 8px; border-radius: 6px;
        font-size: 0.85rem; border-left: 3px solid #ddd;
    }
    .info-item b { display: block; font-size: 1rem; color: #2d3436; }
    
    .legend-row {
        display: flex; justify-content: space-between; padding: 6px 12px;
        margin-bottom: 4px; border-radius: 4px; color: white;
        font-weight: 600; font-size: 0.8rem; align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ETAT ---
if 'route_data' not in st.session_state: st.session_state.route_data = None
if 'last_coords' not in st.session_state: st.session_state.last_coords = None

# --- MOTEUR DE CALCUL (OSRM) ---
def calculate_price_tier(km_route):
    # Logique : On paie pour les kilomètres RÉELS parcourus (Route)
    base_price = 25.00
    fee = 6.00
    color = "#636e72"
    label = "HORS ZONE (>30km)"
    
    # Tri du plus petit au plus grand pour trouver la bonne tranche
    sorted_zones = sorted(ZONES_CONFIG, key=lambda x: x['limit'])
    
    for zone in sorted_zones:
        if km_route <= zone['limit']:
            fee = zone['price']
            color = zone['color']
            label = f"{zone['label']}"
            break
            
    return { "total": base_price + fee, "fee": fee, "color": color, "label": label }

def get_route_osrm(dest_lat, dest_lon):
    # 1. Essai Route Sans Péage/Autoroute
    base_url = f"http://router.project-osrm.org/route/v1/driving/{HOME_COORDS[1]},{HOME_COORDS[0]};{dest_lon},{dest_lat}"
    
    # Paramètres : Exclure autoroutes
    params = {"overview": "full", "geometries": "geojson", "exclude": "motorway,toll"}
    
    final_data = None
    used_highway = False
    
    try:
        r = requests.get(base_url, params=params, timeout=3)
        if r.status_code == 200 and r.json()['code'] == 'Ok':
            final_data = r.json()
        else:
            raise Exception("Fallback")
    except:
        # 2. Si échec (trop loin ou bug serveur), route standard
        try:
            used_highway = True
            r = requests.get(base_url, params={"overview": "full", "geometries": "geojson"}, timeout=3)
            if r.status_code == 200:
                final_data = r.json()
        except:
            pass

    if final_data:
        route = final_data['routes'][0]
        dist_km = round(route['distance'] / 1000, 1)
        duration_min = round(route['duration'] / 60)
        geometry = [(lat, lon) for lon, lat in route['geometry']['coordinates']]
        
        return { 
            "dist_km": dist_km, 
            "duration_min": duration_min, 
            "geometry": geometry, 
            "price_info": calculate_price_tier(dist_km),
            "highway_excluded": not used_highway
        }
    return None

def search_nominatim(address):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        r = requests.get(url, params={"q": address, "format": "json", "limit": 1, "countrycodes": "fr"}, headers={'User-Agent': 'DelepineApp/1.0'})
        if r.status_code == 200 and r.json():
            return float(r.json()[0]['lat']), float(r.json()[0]['lon'])
    except:
        return None

# =========================================================
# 🖥️ INTERFACE
# =========================================================
with st.sidebar:
    st.title("🏠 Delepine Services")
    st.caption("📍 Départ : Auby | 🛣️ Calcul : Km Réel (Hors Péage)")
    
    st.markdown("---")
    
    # Recherche
    c1, c2 = st.columns([3, 1])
    with c1:
        addr = st.text_input("Adresse", placeholder="Ex: Mairie de Douai", label_visibility="collapsed")
    with c2:
        if st.button("🔎", type="primary") and addr:
            coords = search_nominatim(addr)
            if coords:
                st.session_state.last_coords = coords
                st.session_state.route_data = get_route_osrm(coords[0], coords[1])
                st.rerun()
            else:
                st.error("Introuvable")

    # Affichage Résultats
    if st.session_state.route_data:
        d = st.session_state.route_data
        p = d['price_info']
        
        warn_txt = "✅ Route Sans Péage" if d['highway_excluded'] else "⚠️ Route Standard (Optimisée)"
        warn_col = "#2ecc71" if d['highway_excluded'] else "#95a5a6"
        
        st.markdown(f"""
        <div class="price-box" style="border-top-color: {p['color']};">
            <div class="zone-badge" style="background-color: {p['color']};">{p['label']}</div>
            <div class="big-price" style="color: {p['color']};">{p['total']:.2f} €</div>
            <div style="color:#999; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">Total Déplacement</div>
            
            <div class="info-grid">
                <div class="info-item" style="border-color:{p['color']}">📏 Distance Route<b>{d['dist_km']} km</b></div>
                <div class="info-item" style="border-color:{p['color']}">⏱️ Durée Est.<b>{d['duration_min']} min</b></div>
                <div class="info-item" style="border-color:{p['color']}">⛽ Frais Zone<b>{p['fee']:.2f} €</b></div>
                <div class="info-item" style="border-color:{p['color']}">🏠 Forfait Base<b>25.00 €</b></div>
            </div>
            
            <div class="route-warning" style="background:{warn_col}">{warn_txt}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Grille Tarifaire
    st.markdown("---")
    st.markdown("##### 🏷️ Grille Tarifaire (Km Route)")
    for z in sorted(ZONES_CONFIG, key=lambda x: x['limit']):
        price = "Gratuit" if z['price'] == 0 else f"+{z['price']} €"
        st.markdown(f"""
        <div class="legend-row" style="background:{z['color']};">
            <span>{z['label']} (0-{z['limit']} km)</span><span>{price}</span>
        </div>""", unsafe_allow_html=True)
    st.caption("ℹ️ Les zones sur la carte sont ajustées pour refléter la distance réelle par la route (Coeff 1.3).")

# =========================================================
# 🗺️ CARTE
# =========================================================
m = folium.Map(location=HOME_COORDS, zoom_start=11, tiles='CartoDB voyager')

# 1. Cercles Ajustés (Visuel Intelligent)
for z in reversed(ZONES_CONFIG): # Du plus grand au plus petit
    folium.Circle(
        location=HOME_COORDS,
        radius=z['radius'], # Rayon réduit (astuce)
        color=z['color'],
        weight=1,
        fill=True, fill_opacity=0.1,
        tooltip=f"{z['label']} (Limite route: {z['limit']}km)"
    ).add_to(m)

# 2. Marqueurs & Route
folium.Marker(HOME_COORDS, icon=folium.Icon(color="black", icon="home", prefix="fa"), tooltip="Siège").add_to(m)

if st.session_state.route_data:
    folium.PolyLine(
        st.session_state.route_data['geometry'], 
        color="#2d3436", weight=5, opacity=0.8
    ).add_to(m)
    folium.Marker(st.session_state.last_coords, icon=folium.Icon(color="red", icon="user", prefix="fa")).add_to(m)

# 3. Rendu
map_out = st_folium(m, width="100%", height=700)

if map_out['last_clicked']:
    lat, lon = map_out['last_clicked']['lat'], map_out['last_clicked']['lng']
    # Eviter refresh boucle infinie
    if not st.session_state.last_coords or abs(st.session_state.last_coords[0] - lat) > 0.0001:
        st.session_state.last_coords = [lat, lon]
        st.session_state.route_data = get_route_osrm(lat, lon)
        st.rerun()
