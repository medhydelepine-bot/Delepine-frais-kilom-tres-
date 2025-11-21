import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# Configuration de la page
st.set_page_config(page_title="Delepine Services", layout="wide")

# --- CSS pour le style (optionnel mais recommandé) ---
st.markdown("""
    <style>
    .big-font { font-size:30px !important; color: #27ae60; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.image("logo.png", width=150) # Assurez-vous d'avoir l'image
    st.title("Delepine Domicile")
    st.info("📍 Siège : 21 rue Paul Bert, 59950 Auby")
    
    address = st.text_input("Adresse client")
    if st.button("Calculer"):
        st.write("Recherche...")
        # Ici, on mettrait le code pour chercher l'adresse avec Python

# --- COORDONNÉES ---
HOME_COORDS = [50.4137, 3.0568]

# --- CARTE ---
m = folium.Map(location=HOME_COORDS, zoom_start=11)

# Ajout du marqueur domicile
folium.Marker(
    HOME_COORDS, 
    popup="Siège Delepine", 
    icon=folium.Icon(color="green", icon="home")
).add_to(m)

# Ajout des zones (Cercles simples pour l'exemple Python)
folium.Circle(HOME_COORDS, radius=10000, color="#2ecc71", fill=True, fill_opacity=0.2).add_to(m)
folium.Circle(HOME_COORDS, radius=20000, color="#e67e22", fill=True, fill_opacity=0.1).add_to(m)

# --- INTERACTIVITÉ ---
# C'est ici que la magie opère : on affiche la carte et on récupère le clic
output = st_folium(m, width="100%", height=600)

# --- LOGIQUE APRÈS LE CLIC ---
if output["last_clicked"]:
    lat = output["last_clicked"]["lat"]
    lon = output["last_clicked"]["lng"]
    
    st.sidebar.success(f"Clic détecté : {lat:.4f}, {lon:.4f}")
    
    # C'est ici qu'on appellerait l'API de routing en Python
    # Pour calculer la distance et le prix
    distance_mock = 12.5 # Exemple fictif
    prix_mock = 25 + 1.50
    
    st.sidebar.markdown(f'<p class="big-font">{prix_mock} €</p>', unsafe_allow_html=True)
    st.sidebar.write(f"Distance : {distance_mock} km")
