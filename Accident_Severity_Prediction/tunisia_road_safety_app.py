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

# Set page configuration
st.set_page_config(
    page_title="Tunisia Road Safety Navigator",
    page_icon="??",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3D59;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #1E3D59;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .high-risk {
        color: #FF0000;
        font-weight: bold;
    }
    .medium-risk {
        color: #FFA500;
        font-weight: bold;
    }
    .low-risk {
        color: #008000;
        font-weight: bold;
    }
    .audio-container {
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .recommended-route {
        border: 3px solid #FF5722;
        border-radius: 5px;
        padding: 10px;
        background-color: rgba(255, 87, 34, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# App title
st.markdown("<h1 class=\"main-header\">Tunisia Road Safety Navigator</h1>", unsafe_allow_html=True)
st.markdown("Analyze road conditions, predict accident risks, and navigate safely across Tunisia. Now with voice alerts!")

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/c/ce/Flag_of_Tunisia.svg", width=150)
    st.markdown("## Navigation Settings")
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

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start, tiles="OpenStreetMap")
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
            route_color = '#FF5722' if is_best_route else route_item['color']
            route_weight = 7 if is_best_route else route_item['weight']
            route_opacity = 1.0 if is_best_route else 0.8
            
            # Créer un tooltip plus informatif
            tooltip = f"{'? ITINÉRAIRE RECOMMANDÉ: ' if is_best_route else 'Option: '}{route_item['distance']:.1f} km, {route_item['duration']:.1f} min"
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
                        html: '<i class="fa fa-car" style="color:blue;font-size:24px;"></i>',
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
                border:2px solid grey; z-index:9999; font-size:14px;
                background-color:white; padding: 10px;">
        <b>Légende</b><br>
        <i class="fa fa-user" style="color:purple; font-size:15px;"></i> Votre Position IP<br>
        <i class="fa fa-play" style="color:green; font-size:15px;"></i> Départ Itinéraire<br>
        <i class="fa fa-stop" style="color:red; font-size:15px;"></i> Destination Itinéraire<br>
        <i class="fa fa-car" style="color:blue; font-size:15px;"></i> Position sur l'itinéraire<br>
        <i style="background:#FF5722; width:15px; height:15px; display:inline-block;"></i> Itinéraire Recommandé<br>
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
    if weather_labels:
        dominant_weather = mode(weather_labels)
        dominant_class = mode(weather_classes)
        avg_confidence = sum(weather_confidences) / len(weather_confidences)
        return dominant_weather, dominant_class, avg_confidence
    return "Unknown", 0, 0

def get_safety_advice(severity):
    advice = {
        'Medium': "Conditions de conduite normales. Faites preuve de prudence standard.",
        'High': "Conditions dangereuses détectées. Conduisez avec une prudence accrue et réduisez votre vitesse.",
        'Critical': "Conditions extrêmement dangereuses. Envisagez de reporter votre voyage si possible."
    }
    return advice.get(severity, "Impossible de déterminer le niveau de risque.")

# Function to generate audio from text using gTTS and return HTML audio player
def generate_audio_player(text, lang='fr'):
    if not tts_enabled:
        return ""
    
    try:
        # Create a unique filename for this audio
        audio_file_name = f"audio_{uuid.uuid4().hex}.mp3"
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, audio_file_name)
        
        # Generate the audio file
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(audio_path)
        
        # Read the audio file and encode it to base64
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()
        
        # Clean up the temporary file
        try:
            os.remove(audio_path)
        except:
            pass
        
        # Create HTML for audio player
        audio_html = f"""
        <div class="audio-container">
            <audio controls autoplay="true">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                Votre navigateur ne supporte pas l'élément audio.
            </audio>
        </div>
        """
        return audio_html
    except Exception as e:
        st.error(f"Erreur lors de la génération audio: {str(e)}")
        return ""

def main():
    current_ip_lat, current_ip_lon, current_ip_location_name = get_current_location_cached()
    
    st.markdown("<div class=\"info-box\">", unsafe_allow_html=True)
    st.write(f"?? Votre position IP actuelle (utilisée comme point de départ par défaut): **{current_ip_location_name}** (Lat: {current_ip_lat:.4f}, Lon: {current_ip_lon:.4f})")
    st.markdown("</div>", unsafe_allow_html=True)

    if 'last_osrm_start_coords' not in st.session_state: st.session_state.last_osrm_start_coords = None
    if 'last_osrm_dest_coords' not in st.session_state: st.session_state.last_osrm_dest_coords = None
    if 'last_routes_data' not in st.session_state: st.session_state.last_routes_data = None
    if 'last_weather_info' not in st.session_state: st.session_state.last_weather_info = None
    if 'last_severity' not in st.session_state: st.session_state.last_severity = None
    if 'last_speech_text' not in st.session_state: st.session_state.last_speech_text = ""
    if 'best_route_index' not in st.session_state: st.session_state.best_route_index = 0

    st.markdown("<h2 class=\"sub-header\">Analyse des Conditions Routières</h2>", unsafe_allow_html=True)
    uploaded_images = st.file_uploader("Téléchargez des images de route/météo pour analyse", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_images:
        with st.spinner("Analyse des conditions routières à partir des images..."):
            cols = st.columns(min(3, len(uploaded_images)))
            for i, img_file in enumerate(uploaded_images):
                cols[i % len(cols)].image(img_file, caption=f"Image {i+1}", use_column_width=True)
            weather_label, weather_class, confidence = analyze_multiple_images(uploaded_images)
            analysis_location = st.session_state.last_osrm_start_coords if st.session_state.last_osrm_start_coords else (current_ip_lat, current_ip_lon)
            severity_analysis = predict_accident_severity(weather_class, analysis_location)
            weather_info_analysis = (weather_label, confidence)
            st.session_state.last_weather_info = weather_info_analysis
            st.session_state.last_severity = severity_analysis
            
            st.markdown("<div class=\"info-box\">", unsafe_allow_html=True)
            st.write("### Résultats de l'Analyse")
            st.write(f"??? Météo détectée: **{weather_label}** (Confiance: {confidence:.1f}%)")
            risk_message = f"Risque d'accident: {severity_analysis}"
            st.markdown(f"?? {risk_message}", unsafe_allow_html=True)
            safety_advice_message = get_safety_advice(severity_analysis)
            st.write(f"?? **Conseil de sécurité:** {safety_advice_message}")
            
            # Generate and display audio player for the analysis results
            speech_text = f"{risk_message}. {safety_advice_message}"
            if speech_text != st.session_state.last_speech_text:
                audio_player = generate_audio_player(speech_text)
                st.markdown(audio_player, unsafe_allow_html=True)
                st.session_state.last_speech_text = speech_text
            
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<h2 class=\"sub-header\">Navigation</h2>", unsafe_allow_html=True)
    destination_input = st.text_input("Entrez votre destination en Tunisie:", "Sousse", key="destination_input")
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
                            route_title = f"{'? ITINÉRAIRE RECOMMANDÉ' if is_best_route else f'Option {i+1}'}"
                            st.markdown(f"### {route_title}")
                            st.write(f"??? Distance: **{route['distance']:.1f} km**")
                            st.write(f"?? Durée estimée: **{route['duration']:.1f} minutes**")
                            
                            if is_best_route and st.session_state.last_weather_info and st.session_state.last_severity:
                                weather_label, confidence = st.session_state.last_weather_info
                                st.write(f"??? Conditions météo: **{weather_label}** (Confiance: {confidence:.1f}%)")
                                st.write(f"?? Niveau de risque: **{st.session_state.last_severity}**")
                                st.write(f"?? **Conseil:** {get_safety_advice(st.session_state.last_severity)}")
                                
                                # Générer un message audio pour l'itinéraire recommandé
                                if is_best_route:
                                    route_speech = f"Itinéraire recommandé trouvé. Distance: {route['distance']:.1f} kilomètres. Durée estimée: {route['duration']:.1f} minutes. Conditions météo: {weather_label}. {get_safety_advice(st.session_state.last_severity)}"
                                    route_audio = generate_audio_player(route_speech)
                                    st.markdown(route_audio, unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Explication de la logique de sélection d'itinéraire
                        st.markdown("<div class=\"info-box\">", unsafe_allow_html=True)
                        st.markdown("### ?? Logique de Sélection d'Itinéraire")
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

if __name__ == "__main__":
    main()
