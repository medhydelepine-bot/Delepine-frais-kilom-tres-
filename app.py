import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice
from openrouteservice import convert

# =========================================================
# 🔑 CONFIGURATION - À REMPLIR OBLIGATOIREMENT
# =========================================================
# Collez votre clé API OpenRouteService ici (la même que pour la version HTML)
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0=" 

# Coordonnées du siège (Auby)
HOME_COORDS = [50.4137, 3.0568]
# =========================================================

# Configuration de la page
st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

# --- CSS PERSONNALISÉ (Pour le look) ---
st.markdown("""
    <style>
    .price-box {
        background-color: #f0f2f5;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border-left: 5px solid #ccc;
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
        border-bottom: 1px solid #ddd;
        padding-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation du client API
try:
    client = openrouteservice.Client(key=ORS_API_KEY)
except:
    st.error("Clé API manquante ou invalide.")
    client = None

# --- GESTION DE L'ÉTAT (Pour se souvenir du dernier trajet calculé) ---
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
        fee = 6.00 # Ou plus selon vos règles
        color = "#7f8c8d"
        label = "Hors Zone (>30km)"
        
    return {
        "total": base_price + fee,
        "fee": fee,
        "color": color,
        "label": label,
        "km": km
    }

# --- FONCTION CACHÉE POUR LES ZONES (Pour ne pas recharger à chaque clic) ---
@st.cache_data
def get_isochrones():
    if not client: return None
    # Zones inversées (Grand -> Petit) pour l'affichage
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
    except Exception as e:
        st.error(f"Erreur Zones: {e}")
        return None

# --- FONCTION CALCUL ITINÉRAIRE ---
def get_route(dest_lat, dest_lon):
    if not client: return None
    try:
        coords = [[HOME_COORDS[1], HOME_COORDS[0]], [dest_lon, dest_lat]]
        routes = client.directions(coordinates=coords, profile='driving-car', format='geojson')
        
        # Extraction des infos
        summary = routes['features'][0]['properties']['summary']
        dist_km = round(summary['distance'] / 1000, 1)
        duration_min = round(summary['duration'] / 60)
        geometry = routes['features'][0]['geometry']['coordinates']
        
        # Inversion [lon, lat] -> [lat, lon] pour Folium
        decoded_geom = [(lat, lon) for lon, lat in geometry]
        
        return {
            "dist_km": dist_km,
            "duration_min": duration_min,
            "geometry": decoded_geom,
            "price_info": calculate_price_tier(dist_km)
        }
    except Exception as e:
        st.error(f"Erreur Itinéraire: {e}")
        return None


# =========================================================
# 🖥️ INTERFACE SIDEBAR
# =========================================================
with st.sidebar:
    # Logo
    try:
        st.image("logo.png", width=150)
    except:
        st.warning("Image logo.png introuvable")

    st.title("Delepine Services")
    st.markdown("*📍 Siège : 21 rue Paul Bert, 59950 Auby*")
    st.markdown("---")

    # Recherche Adresse
    address_input = st.text_input("Recherche adresse :")
    if st.button("GO") and address_input and client:
        try:
            geocode = client.pelias_search(text=address_input, focus_point=[HOME_COORDS[1], HOME_COORDS[0]])
            if geocode['features']:
                coords = geocode['features'][0]['geometry']['coordinates']
                # Mise à jour de l'état
                st.session_state.last_coords = [coords[1], coords[0]] # Lat, Lon
                st.session_state.route_data = get_route(coords[1], coords[0])
            else:
                st.error("Adresse introuvable")
        except Exception as e:
            st.error("Erreur recherche")

    st.markdown("---")

    # AFFICHAGE RESULTATS
    if st.session_state.route_data:
        data = st.session_state.route_data
        info = data['price_info']
        
        # Injection HTML pour le style dynamique
        html_card = f"""
        <div class="price-box" style="border-left-color: {info['color']};">
            <div class="zone-badge" style="background-color: {info['color']};">{info['label']}</div>
            <div>Total Prestation</div>
            <div class="big-price" style="color: {info['color']};">{info['total']:.2f} €</div>
            <div style="text-align:left; margin-top:15px; font-size:0.9rem; color:#555;">
                <div class="info-row"><span>⏱️ Temps trajet :</span> <b>{data['duration_min']} min</b></div>
                <div class="info-row"><span>📏 Distance :</span> <b>{data['dist_km']} km</b></div>
                <div class="info-row"><span>💼 Base :</span> <b>25.00 €</b></div>
                <div class="info-row"><span>⛽ Supplément :</span> <b>{info['fee']:.2f} €</b></div>
            </div>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)
    
    else:
        st.info("Cliquez sur la carte ou entrez une adresse.")

    # Légende statique
    st.markdown("### Barème")
    st.caption("🟢 0-10km : Inclus")
    st.caption("🟡 10-15km : +1.50€")
    st.caption("🟠 15-20km : +3.00€")
    st.caption("🟧 20-25km : +4.50€")
    st.caption("🔴 25-30km : +6.00€")


# =========================================================
# 🗺️ CARTE PRINCIPALE
# =========================================================

# Création de la carte de base
m = folium.Map(location=HOME_COORDS, zoom_start=10, tiles="CartoDB positron")

# 1. Ajout des Zones (Isochrones)
iso_data = get_isochrones()
if iso_data:
    # Fonction de style pour colorier les zones selon la valeur (distance)
    def style_function(feature):
        val = feature['properties']['value']
        col = "#c0392b" # Defaut Rouge
        if val <= 10000: col = "#2ecc71"
        elif val <= 15000: col = "#f1c40f"
        elif val <= 20000: col = "#e67e22"
        elif val <= 25000: col = "#d35400"
        
        return {
            'fillColor': col,
            'color': col,
            'weight': 1,
            'fillOpacity': 0.15,
            'interactive': False # IMPORTANT: permet de cliquer à travers
        }
    
    folium.GeoJson(iso_data, style_function=style_function).add_to(m)

# 2. Ajout Marqueur Domicile
folium.Marker(
    HOME_COORDS, 
    popup="Siège Delepine", 
    icon=folium.Icon(color="black", icon="home", prefix="fa")
).add_to(m)

# 3. Ajout Trajet si existant
if st.session_state.route_data:
    # Ligne bleue du trajet
    folium.PolyLine(
        locations=st.session_state.route_data['geometry'], 
        color="#2980b9", 
        weight=5, 
        opacity=0.8
    ).add_to(m)
    
    # Marqueur Destination
    folium.Marker(
        st.session_state.last_coords,
        icon=folium.Icon(color="blue", icon="user", prefix="fa")
    ).add_to(m)

# 4. Rendu de la carte et capture du clic
map_output = st_folium(m, width="100%", height=700)

# 5. Logique du Clic (Interactif)
if map_output['last_clicked']:
    clicked_lat = map_output['last_clicked']['lat']
    clicked_lon = map_output['last_clicked']['lng']
    
    # On vérifie si c'est un nouveau clic pour éviter les boucles infinies
    is_new_click = False
    if st.session_state.last_coords is None:
        is_new_click = True
    elif (abs(st.session_state.last_coords[0] - clicked_lat) > 0.0001 or 
          abs(st.session_state.last_coords[1] - clicked_lon) > 0.0001):
        is_new_click = True
        
    if is_new_click:
        st.session_state.last_coords = [clicked_lat, clicked_lon]
        st.session_state.route_data = get_route(clicked_lat, clicked_lon)
        st.rerun() # Recharge la page pour afficher le trajet et le prix
