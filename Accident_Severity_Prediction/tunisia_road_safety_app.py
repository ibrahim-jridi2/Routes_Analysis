import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import folium_static
import polyline
import reverse_geocoder as rg
import geocoder
from geopy.geocoders import Nominatim
from datetime import datetime
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from PIL import Image
from statistics import mode
import onnxruntime as ort
import os
import tempfile
from gtts import gTTS
import base64
import uuid
import time

# Set page configuration uniquement si le script est exécuté directement (pas importé)
if __name__ == "__main__":
    st.set_page_config(
        page_title="Tunisia Road Safety Navigator",
        page_icon="🛣️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Apply custom styling
st.markdown("""
<style>
    /* Palette de couleurs futuriste */
    :root {
        --primary: #3a86ff;
        --secondary: #8338ec;
        --accent: #ff006e;
        --background: #111111;
        --card-bg: #1a1a1a;
        --text: #ffffff;
        --text-secondary: #aaaaaa;
        --success: #06d6a0;
        --warning: #ffbe0b;
        --danger: #ef476f;
    }
    
    /* Styles généraux */
    .main {
        background-color: var(--background);
        color: var(--text);
    }
    
    h1, h2, h3 {
        color: var(--text);
        font-family: 'Orbitron', sans-serif;
        letter-spacing: 1px;
    }
    
    .main-header {
        font-size: 2.5rem;
        color: var(--primary);
        text-align: center;
        margin-bottom: 1rem;
        font-family: 'Orbitron', sans-serif;
    }
    
    .sub-header {
        font-size: 1.5rem;
        color: var(--primary);
        margin-top: 2rem;
        margin-bottom: 1rem;
        font-family: 'Orbitron', sans-serif;
    }
    
    .info-box {
        background: linear-gradient(145deg, var(--card-bg), #222222);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }
    
    .high-risk {
        color: var(--danger);
        font-weight: bold;
    }
    
    .medium-risk {
        color: var(--warning);
        font-weight: bold;
    }
    
    .low-risk {
        color: var(--success);
        font-weight: bold;
    }
    
    .audio-container {
        margin-top: 10px;
        margin-bottom: 10px;
    }
    
    .recommended-route {
        border: 3px solid var(--accent);
        border-radius: 15px;
        padding: 15px;
        background-color: rgba(255, 0, 110, 0.1);
        box-shadow: 0 4px 20px 0 rgba(255, 0, 110, 0.2);
    }
    
    .icon-weather {
        color: var(--primary);
        font-weight: bold;
    }
    
    .icon-location {
        color: var(--secondary);
        font-weight: bold;
    }
    
    .icon-risk {
        color: var(--danger);
        font-weight: bold;
    }
    
    .icon-warning {
        color: var(--warning);
        font-weight: bold;
    }
    
    .icon-road {
        color: var(--primary);
        font-weight: bold;
    }
    
    .icon-time {
        color: var(--success);
        font-weight: bold;
    }
    
    .icon-check {
        color: var(--success);
        font-weight: bold;
    }
    
    .icon-brain {
        color: var(--secondary);
        font-weight: bold;
    }
    
    /* Personnalisation des éléments Streamlit */
    .stButton button {
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px rgba(58, 134, 255, 0.5);
    }
    
    .stSlider div[data-baseweb="slider"] {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    .stSlider div[data-baseweb="slider"] div[role="progressbar"] {
        background-color: var(--primary);
    }
    
    .stSlider div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--accent);
        border: 2px solid white;
    }
    
    /* Animation pour les éléments */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate {
        animation: fadeIn 0.5s ease-out forwards;
    }
    
    /* Ajout de la police Orbitron pour le style futuriste */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&display=swap');
</style>

<!-- Ajout de Font Awesome pour les icônes -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
""", unsafe_allow_html=True)

# App title
st.markdown("<h1 class=\"main-header\">Tunisia Road Safety Navigator</h1>", unsafe_allow_html=True)
st.markdown("<p class='animate' style='text-align: center; color: var(--text-secondary);'>Analyze road conditions, predict accident risks, and navigate safely across Tunisia. Now with voice alerts!</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/c/ce/Flag_of_Tunisia.svg", width=150)
    st.markdown("<h2 style='color: var(--primary); font-family: Orbitron, sans-serif;'>Navigation Settings</h2>", unsafe_allow_html=True)
    app_mode = st.radio(
        "Choose Mode:",
        ["Single Route Analysis", "Multiple Routes Comparison"]
    )
    tts_enabled = st.checkbox("Enable Voice Alerts", value=True)

@st.cache_resource
def load_models():
    try:
        weather_model = load_model("Accident_Severity_Prediction/weather_cnn_model.h5")
        accident_model = ort.InferenceSession("Accident_Severity_Prediction/accident_severity_model.onnx")
        return weather_model, accident_model
    except Exception as e:
        st.error(f"Error loading models: {str(e)}")
        return None, None

weather_model, accident_model = load_models()

weather_labels_mapping = {0: 'Cloudy', 1: 'Foggy', 2: 'Rainy', 3: 'Shine', 4: 'Sunrise'}
severity_mapping = {0: 'Medium', 1: 'High', 2: 'Critical'}
risk_color_mapping = {
    'Medium': 'medium-risk',
    'High': 'high-risk',
    'Critical': 'high-risk'
}

# Définir les poids de risque pour chaque condition météo
weather_risk_weights = {
    'Cloudy': 1.2,    # Nuageux - risque légèrement accru
    'Foggy': 2.0,     # Brouillard - risque élevé
    'Rainy': 1.8,     # Pluie - risque modérément élevé
    'Shine': 1.0,     # Ensoleillé - risque de base
    'Sunrise': 1.3,   # Lever de soleil - visibilité réduite
    'Unknown': 1.5    # Inconnu - risque moyen par défaut
}

# Définir les poids de risque pour chaque niveau de gravité d'accident
severity_risk_weights = {
    'Medium': 1.5,    # Risque moyen
    'High': 2.5,      # Risque élevé
    'Critical': 4.0,  # Risque critique
    'Unknown': 2.0    # Inconnu - risque moyen-élevé par défaut
}

@st.cache_data(ttl=300)
def get_current_location_cached():
    try:
        tunis_coords = (36.8065, 10.1815)
        location_name = "Tunis (Default)"
        g = geocoder.ip('me')
        if g.latlng and 30 < g.latlng[0] < 38 and 7 < g.latlng[1] < 12:
            loc_info = rg.search(g.latlng)[0]
            return g.latlng[0], g.latlng[1], loc_info.get('name', 'Current Location (Tunisia)')
        return tunis_coords[0], tunis_coords[1], location_name
    except Exception as e:
        return 36.8065, 10.1815, "Tunis (Default)"

def analyze_image(uploaded_image):
    try:
        image = Image.open(uploaded_image).resize((128, 128))
        img_array = img_to_array(image) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        weather_pred = weather_model.predict(img_array)
        weather_class = np.argmax(weather_pred)
        weather_label = weather_labels_mapping.get(weather_class, "Unknown")
        weather_confidence = np.max(weather_pred) * 100
        return weather_label, weather_class, weather_confidence
    except Exception as e:
        st.error(f"Error analyzing image: {str(e)}")
        return "Unknown", 0, 0

def predict_accident_severity(weather_class, location_coords):
    try:
        current_date = datetime.now().toordinal()
        current_day_of_week = datetime.now().weekday()
        input_dict = {
            'Day_of_Week': [current_day_of_week], 'Date': [current_date],
            'Latitude': [location_coords[0]], 'Longitude': [location_coords[1]],
            'Number_of_Casualties': [3], 'Number_of_Vehicles': [100],
            'Road_Surface_Conditions': [2], 'Weather_Conditions': [weather_class]
        }
        input_df = pd.DataFrame(input_dict)
        input_np = input_df.to_numpy().astype(np.float32)
        input_name = accident_model.get_inputs()[0].name
        output = accident_model.run(None, {input_name: input_np})[0]
        severity_pred = int(np.argmax(output))
        severity_label = severity_mapping.get(severity_pred, 'Unknown')
        return severity_label
    except Exception as e:
        st.error(f"Error predicting accident severity: {str(e)}")
        return "Unknown"

def get_routes(start_coords, end_coords, alternatives=True):
    try:
        alt_param = "alternatives=true" if alternatives else "alternatives=false"
        url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}?{alt_param}&overview=full&steps=true"
        response = requests.get(url, timeout=30)
        data = response.json()
        if data.get('code') == 'Ok':
            routes_data = []
            colors = ['#1E90FF', '#32CD32', '#9932CC']
            weights = [5, 4, 3]
            for i, route_item in enumerate(data['routes']):
                route_coords = polyline.decode(route_item['geometry'])
                if route_coords:
                    routes_data.append({
                        'coords': route_coords,
                        'distance': route_item['distance']/1000,
                        'duration': route_item['duration']/60,
                        'color': colors[i % len(colors)],
                        'weight': weights[i % len(weights)],
                        'steps': route_item.get('steps', [])
                    })
            return routes_data if routes_data else None
        else:
            st.warning(f"Could not find routes from OSRM. Response: {data.get('message', data.get('code'))}")
            return None
    except Exception as e:
        st.error(f"Routing error: {str(e)}")
        return None

# Nouvelle fonction pour évaluer les itinéraires en fonction de la gravité des accidents et de la météo
def evaluate_routes(routes, weather_info, severity):
    if not routes or not weather_info or not severity:
        return 0  # Par défaut, retourne le premier itinéraire si les données sont insuffisantes
    
    weather_label, weather_confidence = weather_info
    weather_risk = weather_risk_weights.get(weather_label, weather_risk_weights['Unknown'])
    severity_risk = severity_risk_weights.get(severity, severity_risk_weights['Unknown'])
    
    # Calculer un score pour chaque itinéraire (plus le score est bas, meilleur est l'itinéraire)
    route_scores = []
    for i, route in enumerate(routes):
        # Facteurs de base: distance et durée
        distance_factor = route['distance'] / 10  # Normaliser la distance (en km)
        duration_factor = route['duration'] / 60  # Normaliser la durée (en minutes)
        
        # Facteur de risque basé sur la météo et la gravité des accidents
        risk_factor = weather_risk * severity_risk
        
        # Score final (combinaison pondérée des facteurs)
        # Plus le risque est élevé, plus on pénalise les itinéraires longs
        score = (distance_factor * 0.3 + duration_factor * 0.2) * risk_factor
        
        route_scores.append((i, score))
    
    # Trier les itinéraires par score (du plus bas au plus élevé)
    route_scores.sort(key=lambda x: x[1])
    
    # Retourner l'index du meilleur itinéraire
    return route_scores[0][0]

def create_map(start_coords, end_coords, current_ip_location_coords, routes=None, weather_info=None, severity=None):
    if start_coords and end_coords:
        center_lat = (start_coords[0] + end_coords[0]) / 2
        center_lon = (start_coords[1] + end_coords[1]) / 2
        zoom_start = 9
    elif current_ip_location_coords:
        center_lat, center_lon = current_ip_location_coords
        zoom_start = 12
    else:
        center_lat, center_lon = (36.8065, 10.1815)
        zoom_start = 7

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start, tiles="CartoDB dark_matter")
    folium.TileLayer('CartoDB positron', name='Light Map').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(m)
    folium.TileLayer('Stamen Terrain', name='Terrain Map').add_to(m)

    if current_ip_location_coords:
        folium.Marker(
            current_ip_location_coords, 
            tooltip="Votre Position IP Actuelle", 
            popup=f"Position IP: {current_ip_location_coords[0]:.4f}, {current_ip_location_coords[1]:.4f}", 
            icon=folium.Icon(color='purple', icon='user', prefix='fa')
        ).add_to(m)

    if start_coords and end_coords:
        start_tooltip = "Départ de l'itinéraire"
        if weather_info:
            start_tooltip += f"\nWeather: {weather_info[0]} ({weather_info[1]:.1f}%)"
            start_tooltip += f"\nRisk: {severity}"
        folium.Marker(start_coords, tooltip=start_tooltip, popup=f"Départ Itinéraire: {start_coords[0]:.4f}, {start_coords[1]:.4f}", icon=folium.Icon(color='green', icon='play')).add_to(m)
        folium.Marker(end_coords, tooltip="Destination de l'itinéraire", popup=f"Destination Itinéraire: {end_coords[0]:.4f}, {end_coords[1]:.4f}", icon=folium.Icon(color='red', icon='stop')).add_to(m)

    if routes:
        # Évaluer les itinéraires et obtenir l'index du meilleur itinéraire
        best_route_index = evaluate_routes(routes, weather_info, severity)
        
        for i, route_item in enumerate(routes):
            is_best_route = (i == best_route_index)
            
            # Modifier l'apparence de l'itinéraire recommandé
            route_color = '#FF006E' if is_best_route else route_item['color']
            route_weight = 7 if is_best_route else route_item['weight']
            route_opacity = 1.0 if is_best_route else 0.8
            
            # Créer un tooltip plus informatif
            tooltip = f"{'ITINÉRAIRE RECOMMANDÉ: ' if is_best_route else 'Option: '}{route_item['distance']:.1f} km, {route_item['duration']:.1f} min"
            if is_best_route and weather_info and severity:
                tooltip += f"\nConditions: {weather_info[0]}, Risque: {severity}"
            
            # Ajouter l'itinéraire à la carte
            route_line = folium.PolyLine(
                route_item['coords'], 
                color=route_color, 
                weight=route_weight, 
                opacity=route_opacity, 
                tooltip=tooltip, 
                dash_array='5, 5' if not is_best_route and i > 0 else None
            ).add_to(m)
            
            # Ajouter un marqueur mobile pour l'itinéraire recommandé
            if is_best_route:
                # Ajouter un marqueur au début de l'itinéraire qui sera déplacé
                route_marker_id = f"route_marker_{i}"
                folium.Marker(
                    route_item['coords'][0],
                    tooltip="Votre position sur l'itinéraire",
                    icon=folium.Icon(color='blue', icon='car', prefix='fa'),
                    popup="Déplacement automatique le long de l'itinéraire recommandé"
                ).add_to(m)
                
                # Ajouter un script pour déplacer le marqueur le long de l'itinéraire
                route_coords_js = [[lat, lng] for lat, lng in route_item['coords']]
                js_code = f"""
                <script>
                // Fonction pour déplacer le marqueur le long de l'itinéraire
                var routeCoords = {route_coords_js};
                var currentIdx = 0;
                var movingMarker = L.marker(routeCoords[0], {{
                    icon: L.divIcon({{
                        html: '<i class="fa fa-car" style="color:#3a86ff;font-size:24px;"></i>',
                        iconSize: [24, 24],
                        className: 'moving-marker'
                    }})
                }}).addTo(map);
                
                function moveMarker() {{
                    if (currentIdx < routeCoords.length - 1) {{
                        currentIdx++;
                        movingMarker.setLatLng(routeCoords[currentIdx]);
                        setTimeout(moveMarker, 300);  // Vitesse de déplacement
                    }}
                }}
                
                // Démarrer le déplacement après 2 secondes
                setTimeout(moveMarker, 2000);
                </script>
                """
                m.get_root().html.add_child(folium.Element(js_code))
    elif start_coords and end_coords:
        folium.PolyLine([start_coords, end_coords], color='gray', weight=3, opacity=0.8, dash_array='5, 5', tooltip="Ligne directe (pas d'itinéraire OSRM trouvé)").add_to(m)
    
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; width: 220px;
                border:2px solid rgba(255, 255, 255, 0.1); z-index:9999; font-size:14px;
                background-color:rgba(26, 26, 26, 0.8); padding: 10px; border-radius: 10px;
                box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.37);">
        <b style="color: #3a86ff;">Légende</b><br>
        <i class="fa fa-user" style="color:#8338ec; font-size:15px;"></i> Votre Position IP<br>
        <i class="fa fa-play" style="color:#06d6a0; font-size:15px;"></i> Départ Itinéraire<br>
        <i class="fa fa-stop" style="color:#ef476f; font-size:15px;"></i> Destination Itinéraire<br>
        <i class="fa fa-car" style="color:#3a86ff; font-size:15px;"></i> Position sur l'itinéraire<br>
        <i style="background:#FF006E; width:15px; height:15px; display:inline-block;"></i> Itinéraire Recommandé<br>
        <i style="background:#1E90FF; width:15px; height:15px; display:inline-block;"></i> Itinéraire Alternatif 1<br>
        <i style="background:#32CD32; width:15px; height:15px; display:inline-block;"></i> Itinéraire Alternatif 2<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl().add_to(m)
    return m

def analyze_multiple_images(uploaded_images):
    weather_classes, weather_labels, weather_confidences = [], [], []
    for i, img_file in enumerate(uploaded_images):
        weather_label, weather_class, weather_confidence = analyze_image(img_file)
        weather_classes.append(weather_class)
        weather_labels.append(weather_label)
        weather_confidences.append(weather_confidence)
    
    # Déterminer la classe météo dominante
    if weather_classes:
        try:
            dominant_class = mode(weather_classes)
            dominant_label = weather_labels_mapping.get(dominant_class, "Unknown")
            avg_confidence = sum(weather_confidences) / len(weather_confidences)
            return dominant_label, dominant_class, avg_confidence
        except:
            # Si mode() échoue (ex: plusieurs modes), prendre la première classe
            return weather_labels[0], weather_classes[0], weather_confidences[0]
    return "Unknown", 0, 0

def get_safety_advice(severity):
    if severity == "Critical":
        return "Conditions très dangereuses. Évitez de conduire si possible ou redoublez de prudence."
    elif severity == "High":
        return "Risque élevé d'accidents. Conduisez lentement et maintenez une distance de sécurité accrue."
    elif severity == "Medium":
        return "Conditions modérément risquées. Restez vigilant et respectez les limitations de vitesse."
    else:
        return "Conditions inconnues. Conduisez prudemment."

def generate_audio_player(text):
    try:
        # Créer un fichier temporaire pour l'audio
        temp_dir = tempfile.gettempdir()
        audio_file = os.path.join(temp_dir, f"audio_{uuid.uuid4()}.mp3")
        
        # Générer l'audio avec gTTS
        tts = gTTS(text=text, lang='fr', slow=False)
        tts.save(audio_file)
        
        # Lire le fichier audio et l'encoder en base64
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()
        
        # Créer le lecteur audio HTML
        audio_player = f"""
        <div class="audio-container">
            <audio controls autoplay style="width: 100%;">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                Votre navigateur ne supporte pas l'élément audio.
            </audio>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">Message vocal automatique</div>
        </div>
        """
        
        # Supprimer le fichier temporaire
        os.remove(audio_file)
        
        return audio_player
    except Exception as e:
        st.error(f"Erreur lors de la génération de l'audio: {str(e)}")
        return ""

def main():
    # Initialiser les variables de session
    if 'last_osrm_start_coords' not in st.session_state:
        st.session_state.last_osrm_start_coords = None
    if 'last_osrm_dest_coords' not in st.session_state:
        st.session_state.last_osrm_dest_coords = None
    if 'last_routes_data' not in st.session_state:
        st.session_state.last_routes_data = None
    if 'last_weather_info' not in st.session_state:
        st.session_state.last_weather_info = None
    if 'last_severity' not in st.session_state:
        st.session_state.last_severity = None
    if 'best_route_index' not in st.session_state:
        st.session_state.best_route_index = 0
    
    # Obtenir la position IP actuelle
    current_ip_lat, current_ip_lon, current_ip_location_name = get_current_location_cached()
    
    # Conteneur principal avec animation
    st.markdown("<div class='animate'>", unsafe_allow_html=True)
    
    # Section d'analyse des conditions météorologiques
    st.markdown("<h2 class=\"sub-header\"><i class=\"fas fa-cloud-sun\"></i> Analyse des Conditions Météorologiques</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.write("<span class='icon-location'>[POSITION]</span> Position IP détectée: **{}** (Lat: {:.4f}, Lon: {:.4f})".format(
            current_ip_location_name, current_ip_lat, current_ip_lon
        ), unsafe_allow_html=True)
        
        uploaded_images = st.file_uploader("Téléchargez des images des conditions météorologiques actuelles", 
                                         type=["jpg", "jpeg", "png"], 
                                         accept_multiple_files=True)
        
        if uploaded_images:
            with st.spinner("Analyse des images en cours..."):
                weather_label, weather_class, weather_confidence = analyze_multiple_images(uploaded_images)
                st.session_state.last_weather_info = (weather_label, weather_confidence)
                
                # Prédire la gravité des accidents
                severity = predict_accident_severity(weather_class, (current_ip_lat, current_ip_lon))
                st.session_state.last_severity = severity
                
                st.write(f"<span class='icon-weather'>[MÉTÉO]</span> Conditions météo détectées: **{weather_label}** (Confiance: {weather_confidence:.1f}%)", unsafe_allow_html=True)
                st.write(f"<span class='icon-risk'>[RISQUE]</span> Niveau de risque d'accident prédit: <span class='{risk_color_mapping.get(severity, '')}'>{severity}</span>", unsafe_allow_html=True)
                st.write(f"<span class='icon-warning'>[CONSEIL]</span> **{get_safety_advice(severity)}**", unsafe_allow_html=True)
                
                # Générer un message audio pour les alertes vocales
                if tts_enabled:
                    safety_speech = f"Alerte de sécurité routière. Conditions météo détectées: {weather_label}. Niveau de risque d'accident: {severity}. {get_safety_advice(severity)}"
                    safety_audio = generate_audio_player(safety_speech)
                    st.markdown(safety_audio, unsafe_allow_html=True)
        else:
            st.info("Veuillez télécharger des images des conditions météorologiques actuelles pour l'analyse.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        if uploaded_images:
            st.write("### Images analysées")
            image_cols = st.columns(min(3, len(uploaded_images)))
            for i, img_file in enumerate(uploaded_images):
                with image_cols[i % 3]:
                    st.image(img_file, caption=f"Image {i+1}", use_column_width=True)
        else:
            st.markdown("""
            ### Comment ça fonctionne
            
            1. **Téléchargez des images** des conditions météorologiques actuelles
            2. Notre **IA analysera** les conditions météo visibles
            3. Le système **prédit le niveau de risque** d'accident basé sur les conditions
            4. Vous recevrez des **conseils de sécurité** adaptés
            
            Pour de meilleurs résultats, téléchargez plusieurs images prises à l'extérieur montrant clairement le ciel et les conditions routières.
            """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Section de planification d'itinéraire
    st.markdown("<h2 class=\"sub-header\"><i class=\"fas fa-route\"></i> Planification d'Itinéraire Sécurisé</h2>", unsafe_allow_html=True)
    
    # Entrée de destination
    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    destination_input = st.text_input("Entrez votre destination en Tunisie", "Hammamet, Tunisia")
    
    map_placeholder = st.empty()

    if st.button("Trouver les Itinéraires", key="find_routes_btn"):
        st.session_state.last_osrm_start_coords = (current_ip_lat, current_ip_lon)
        st.session_state.last_routes_data = None
        st.session_state.last_osrm_dest_coords = None
        with st.spinner("Recherche d'itinéraires..."):
            geolocator = Nominatim(user_agent="tunisia_road_safety_app_gtts_v1")
            try:
                dest_location_obj = geolocator.geocode(f"{destination_input}, Tunisia")
                if dest_location_obj:
                    dest_lat, dest_lon = dest_location_obj.latitude, dest_location_obj.longitude
                    st.session_state.last_osrm_dest_coords = (dest_lat, dest_lon)
                    routes_data = get_routes(st.session_state.last_osrm_start_coords, st.session_state.last_osrm_dest_coords)
                    st.session_state.last_routes_data = routes_data
                    
                    # Évaluer les itinéraires et obtenir l'index du meilleur itinéraire
                    if routes_data and st.session_state.last_weather_info and st.session_state.last_severity:
                        best_route_index = evaluate_routes(routes_data, st.session_state.last_weather_info, st.session_state.last_severity)
                        st.session_state.best_route_index = best_route_index
                    
                    if routes_data:
                        m = create_map(
                            st.session_state.last_osrm_start_coords, 
                            st.session_state.last_osrm_dest_coords, 
                            (current_ip_lat, current_ip_lon), 
                            routes_data, 
                            st.session_state.last_weather_info, 
                            st.session_state.last_severity
                        )
                        folium_static(m, width=1200, height=600)
                        
                        # Afficher les détails des itinéraires avec mise en évidence du meilleur itinéraire
                        st.markdown("<h3 class=\"sub-header\">Détails des Itinéraires</h3>", unsafe_allow_html=True)
                        
                        for i, route in enumerate(routes_data):
                            is_best_route = (i == st.session_state.best_route_index)
                            route_class = "recommended-route" if is_best_route else ""
                            
                            st.markdown(f"<div class='{route_class}'>", unsafe_allow_html=True)
                            route_title = f"{'[RECOMMANDÉ] ITINÉRAIRE RECOMMANDÉ' if is_best_route else f'Option {i+1}'}"
                            st.markdown(f"### {route_title}")
                            st.write(f"<span class='icon-road'>[DISTANCE]</span> Distance: **{route['distance']:.1f} km**", unsafe_allow_html=True)
                            st.write(f"<span class='icon-time'>[DURÉE]</span> Durée estimée: **{route['duration']:.1f} minutes**", unsafe_allow_html=True)
                            
                            if is_best_route and st.session_state.last_weather_info and st.session_state.last_severity:
                                weather_label, confidence = st.session_state.last_weather_info
                                st.write(f"<span class='icon-weather'>[MÉTÉO]</span> Conditions météo: **{weather_label}** (Confiance: {confidence:.1f}%)", unsafe_allow_html=True)
                                st.write(f"<span class='icon-risk'>[RISQUE]</span> Niveau de risque: **{st.session_state.last_severity}**", unsafe_allow_html=True)
                                st.write(f"<span class='icon-warning'>[CONSEIL]</span> **Conseil:** {get_safety_advice(st.session_state.last_severity)}", unsafe_allow_html=True)
                                
                                # Générer un message audio pour l'itinéraire recommandé
                                if is_best_route:
                                    route_speech = f"Itinéraire recommandé trouvé. Distance: {route['distance']:.1f} kilomètres. Durée estimée: {route['duration']:.1f} minutes. Conditions météo: {weather_label}. {get_safety_advice(st.session_state.last_severity)}"
                                    route_audio = generate_audio_player(route_speech)
                                    st.markdown(route_audio, unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Explication de la logique de sélection d'itinéraire
                        st.markdown("<div class=\"info-box\">", unsafe_allow_html=True)
                        st.markdown("<h3><span class='icon-brain'>[LOGIQUE]</span> Logique de Sélection d'Itinéraire</h3>", unsafe_allow_html=True)
                        st.write("""
                        L'itinéraire recommandé est sélectionné en fonction de plusieurs facteurs:
                        - **Distance et durée** du trajet
                        - **Conditions météorologiques** actuelles (plus risquées: brouillard, pluie)
                        - **Niveau de risque d'accident** prédit pour la zone
                        
                        Notre algorithme calcule un score de risque pour chaque itinéraire et recommande celui qui offre le meilleur équilibre entre sécurité et efficacité.
                        """)
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.error("Impossible de trouver des itinéraires pour cette destination. Veuillez essayer une autre destination.")
                else:
                    st.error(f"Impossible de trouver la localisation: {destination_input}, Tunisia")
            except Exception as e:
                st.error(f"Erreur lors de la recherche d'itinéraires: {str(e)}")
    
    # Afficher la carte avec les données précédentes si disponibles
    elif st.session_state.last_osrm_start_coords and st.session_state.last_osrm_dest_coords and st.session_state.last_routes_data:
        m = create_map(
            st.session_state.last_osrm_start_coords, 
            st.session_state.last_osrm_dest_coords, 
            (current_ip_lat, current_ip_lon), 
            st.session_state.last_routes_data, 
            st.session_state.last_weather_info, 
            st.session_state.last_severity
        )
        folium_static(m, width=1200, height=600)
    else:
        # Afficher une carte centrée sur la position IP actuelle
        m = create_map(None, None, (current_ip_lat, current_ip_lon))
        folium_static(m, width=1200, height=600)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # Fermer le conteneur principal avec animation

if __name__ == "__main__":
    main()
