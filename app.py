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

# Ta clé OpenRouteService (Utilisée juste UNE fois pour la mémoire)
# J'ai remis celle de ton fichier d'origine.
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0="

# Configuration des Prix
ZONES_CONFIG = [
    {"dist": 30000, "price": 6.00, "color": "#d63031", "label": "Zone 5 (30km)"},
    {"dist": 25000, "price": 4.50, "color": "#e056fd", "label": "Zone 4 (25km)"},
    {"dist": 20000, "price": 3.00, "color": "#fdcb6e", "label": "Zone 3 (20km)"},
    {"dist": 15000, "price": 1.50, "color": "#0984e3", "label": "Zone 2 (15km)"},
    {"dist": 10000, "price": 0.00, "color": "#00b894", "label": "Zone 1 (10km)"},
]

# Fichier de sauvegarde des zones (Pour ne plus utiliser la clé)
ZONE_FILE = "zones_memoire.json"

# =========================================================
# 🛠️ FONCTIONS
# =========================================================

def get_cached_isochrones():
    """
    Système intelligent : 
    1. Regarde si le fichier 'zones_memoire.json' existe.
    2. Si OUI : Charge les zones sans clé API (Rapide & Gratuit).
    3. Si NON : Utilise la clé UNE fois pour les télécharger et les sauver.
    """
    # 1. Essai de chargement depuis la mémoire
    if os.path.exists(ZONE_FILE):
        try:
            with open(ZONE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass # Si fichier corrompu, on re-télécharge

    # 2. Téléchargement depuis OpenRouteService (Fournisseur "Tache d'huile")
    # C'est le seul moment où la clé est nécessaire.
    try:
        headers = {
            'Authorization': ORS_API_KEY,
            'Content-Type': 'application/json'
        }
        body = {
            "locations": [[HOME_COORDS[1], HOME_COORDS[0]]],
            "range": [z["dist"] for z in ZONES_CONFIG],
            "range_type": "distance",
            "units": "m",
            "smoothing": 5
        }
        # Appel API
        r = requests.post('https://api.openrouteservice.org/v2/isochrones/driving-car', json=body, headers=headers)
        
        if r.status_code == 200:
            data = r.json()
            # 3. Sauvegarde immédiate dans le fichier
            with open(ZONE_FILE, 'w') as f:
                json.dump(data, f)
            return data
        else:
            st.error(f"Erreur API Zone: {r.text}")
            return None
    except Exception as e:
        st.error(f"Erreur connexion: {e}")
        return None

def get_route_osrm(dest_lat, dest_lon):
    """Calcul itinéraire via OSRM (Gratuit, Sans clé, Hors péage)"""
    base_url = f"http://router.project-osrm.org/route/v1/driving/{HOME_COORDS[1]},{HOME_COORDS[0]};{dest_lon},{dest_lat}"
    
    # On force l'exclusion des autoroutes/péages
    params = {"overview": "full", "geometries": "geojson", "exclude": "motorway,toll"}
    
    used_highway = False
    final_data = None

    try:
        # Tentative 1 : Sans péage
        r = requests.get(base_url, params=params, timeout=4)
        if r.status_code == 200 and r.json()['code'] == 'Ok':
            final_data = r.json()
        else:
            raise Exception("Fallback")
    except:
        # Tentative 2 : Route normale si "sans péage" est impossible
        used_highway = True
        try:
            r = requests.get(base_url, params={"overview": "full", "geometries": "geojson"}, timeout=4)
            if r.status_code == 200:
                final_data = r.json()
        except:
            pass

    if final_data:
        route = final_data['routes'][0]
        dist_km = round(route['distance'] / 1000, 1)
        duration_min = round(route['duration'] / 60)
        geometry = [(lat, lon) for lon, lat in route['geometry']['coordinates']]
        
        # Calcul du prix selon la distance réelle parcourue
        price_info = calculate_price(dist_km)
        
        return {
            "dist_km": dist_km,
            "duration_min": duration_min,
            "geometry": geometry,
            "price_info": price_info,
            "toll_free": not used_highway
        }
    return None

def calculate_price(km):
    base = 25.00
    fee = 6.00
    label = "Hors Zone (>30km)"
    color = "#636e72"
    
    # On trie les zones pour trouver la bonne
    # Attention : la config est en mètres, on compare en km
    sorted_zones = sorted(ZONES_CONFIG, key=lambda x: x['dist'])
    
    for zone in sorted_zones:
        limit_km = zone['dist'] / 1000
        if km <= limit_km:
            fee = zone['price']
            color = zone['color']
            label = zone['label']
            break
            
    return {"total": base + fee, "fee": fee, "color": color, "label": label}

def search_nominatim(address):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        r = requests.get(url, params={"q": address, "format": "json", "limit": 1, "countrycodes": "fr"}, headers={'User-Agent': 'DelepineApp/1.0'})
        if r.status_code == 200 and r.json():
            return float(r.json()[0]['lat']), float(r.json()[0]['lon'])
    except:
        return None

# =========================================================
# 🖥️ APPLICATION
# =========================================================
st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

# CSS Pro
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

# Session
if 'route_data' not in st.session_state: st.session_state.route_data = None
if 'last_coords' not in st.session_state: st.session_state.last_coords = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏠 Delepine Services")
    st.caption("📍 Départ : Auby (Maison)")
    
    # Indicateur de Mémoire des Zones
    if os.path.exists(ZONE_FILE):
        st.success("✅ Zones chargées depuis la mémoire (Pas de clé requise)", icon="💾")
    else:
        st.warning("⚠️ Premier lancement : Clé requise pour générer la mémoire.", icon="🔑")

    st.markdown("---")
    
    # Recherche
    col1, col2 = st.columns([3, 1])
    with col1:
        addr = st.text_input("Adresse", placeholder="Ville, Rue...", label_visibility="collapsed")
    with col2:
        if st.button("🔎", type="primary") and addr:
            coords = search_nominatim(addr)
            if coords:
                st.session_state.last_coords = coords
                st.session_state.route_data = get_route_osrm(coords[0], coords[1])
                st.rerun()
            else:
                st.error("Introuvable")

    # Résultat
    if st.session_state.route_data:
        d = st.session_state.route_data
        p = d['price_info']
        
        warn_msg = "✅ Itinéraire Sans Péage" if d['toll_free'] else "⚠️ Itinéraire Standard (Péage possible)"
        
        st.markdown(f"""
        <div class="price-box" style="border-top-color: {p['color']};">
            <div class="zone-badge" style="background-color: {p['color']};">{p['label']}</div>
            <div class="big-price" style="color: {p['color']};">{p['total']:.2f} €</div>
            <div style="font-size:0.9rem; color:#666;">
                Distance réelle : <b>{d['dist_km']} km</b><br>
                Durée : <b>{d['duration_min']} min</b>
            </div>
            <div style="margin-top:10px; font-size:0.75rem; background:#eee; padding:5px; border-radius:4px;">
                {warn_msg}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Légende
    st.markdown("---")
    st.markdown("##### 🏷️ Tarifs Zones")
    for z in sorted(ZONES_CONFIG, key=lambda x: x['dist']):
        price_txt = "Gratuit" if z['price'] == 0 else f"+{z['price']} €"
        dist_km = int(z['dist']/1000)
        st.markdown(f'<div class="legend-row" style="background:{z["color"]}">'
                    f'<span>Zone {dist_km} km</span><span>{price_txt}</span></div>', 
                    unsafe_allow_html=True)
    st.markdown('<div class="legend-row" style="background:#636e72">'
                '<span>Hors Zone</span><span>+6.00 €</span></div>', unsafe_allow_html=True)

# --- MAP ---
m = folium.Map(location=HOME_COORDS, zoom_start=11, tiles='CartoDB voyager')

# 1. Affichage des Zones (Isochrones "Tache d'huile")
zones_json = get_cached_isochrones()

if zones_json:
    # Fonction de style pour colorier les zones selon la valeur (distance)
    def style_function(feature):
        val = feature['properties']['value']
        color = "#636e72" # Defaut
        # On cherche la couleur correspondante dans la config
        # Les isochrones ORS retournent la valeur en mètres
        for z in sorted(ZONES_CONFIG, key=lambda x: x['dist']):
            if val <= z['dist']:
                color = z['color']
                break
        return {'fillColor': color, 'color': color, 'weight': 1.5, 'fillOpacity': 0.15}

    folium.GeoJson(
        zones_json,
        style_function=style_function,
        name="Zones de Chalandise"
    ).add_to(m)

# 2. Marqueurs et Route
folium.Marker(HOME_COORDS, icon=folium.Icon(color="black", icon="home", prefix="fa"), tooltip="Siège").add_to(m)

if st.session_state.route_data:
    # Ligne de trajet
    folium.PolyLine(
        st.session_state.route_data['geometry'],
        color="#2d3436", weight=5, opacity=0.8
    ).add_to(m)
    # Marqueur Arrivée
    folium.Marker(
        st.session_state.last_coords,
        icon=folium.Icon(color="red", icon="user", prefix="fa")
    ).add_to(m)

st_folium(m, width="100%", height=700)
