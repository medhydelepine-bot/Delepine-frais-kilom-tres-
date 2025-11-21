import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# =========================================================
# 🔑 CONFIGURATION
# =========================================================
# ⚠️ REMPLACE LA CLÉ CI-DESSOUS PAR TA VRAIE CLÉ OPENROUTESERVICE (5b3...)
# Celle d'origine (eyJ...) ne fonctionnera pas car c'est un format incorrect.
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI5Yjg3NDA2NjI1NzRhNjFhNzA0ZmZjMTg2Nzc5ZmMyIiwiaCI6Im11cm11cjY0In0=" 

# Coordonnées EXACTES de votre maison (Auby)
HOME_COORDS = [50.414787, 3.056332]

# =========================================================

st.set_page_config(page_title="Delepine Services", page_icon="🏠", layout="wide")

# --- CSS (Design Global) ---
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

# --- CONNEXION API ---
client = None
if ORS_API_KEY and ORS_API_KEY != "TA_CLE_API_ICI" and not ORS_API_KEY.startswith("eyJ"):
    try:
        client = openrouteservice.Client(key=ORS_API_KEY)
    except Exception as e:
        st.error(f"Erreur de connexion API : {e}")
elif ORS_API_KEY.startswith("eyJ"):
    st.warning("⚠️ Format de clé API incorrect. Utilisez une clé standard OpenRouteService (commençant par '5b3...').")

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
    
    # Ces conditions doivent correspondre à la légende
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
        except:
            st.error("Erreur de recherche")

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
# 🗺️ CARTE & LÉGENDE
# =========================================================

# 1. Configuration HTML de la légende
# Ce bloc HTML/CSS va venir se superposer à la carte
LEGEND_HTML = """
<style>
    .map-overlay {
        position: relative;
        width: 100%;
        top: -20px; /* Remonte un peu pour coller à la carte */
        height: 0; /* Ne prend pas de place dans le flux */
        z-index: 999;
        pointer-events: none; /* Laisse passer les clics */
    }
    .legend-box {
        position: absolute;
        bottom: 40px;
        left: 20px;
        background: rgba(255, 255, 255, 0.9);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        font-family: sans-serif;
        pointer-events: auto; /* Réactive les clics sur la légende */
        backdrop-filter: blur(4px);
        border: 1px solid #eee;
        min-width: 160px;
    }
    .legend-title {
        font-weight: bold;
        font-size: 14px;
        margin-bottom: 8px;
        color: #333;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 4px;
        font-size: 12px;
        color: #555;
    }
    .color-dot {
        width: 15px;
        height: 15px;
        border-radius: 4px;
        margin-right: 8px;
    }
</style>
<div class="
