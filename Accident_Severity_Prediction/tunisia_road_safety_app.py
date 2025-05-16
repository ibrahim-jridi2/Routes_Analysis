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

# Set page configuration
st.set_page_config(
    page_title="Tunisia Road Safety Navigator",
    page_icon="🔊",
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
        weather_model = load_model("weather_cnn_model.h5")
        accident_model = ort.InferenceSession("accident_severity_model.onnx")
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
                        'weight': weights[i % len(weights)]
                    })
            return routes_data if routes_data else None
        else:
            st.warning(f"Could not find routes from OSRM. Response: {data.get('message', data.get('code'))}")
            return None
    except Exception as e:
        st.error(f"Routing error: {str(e)}")
        return None

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
        for i, route_item in enumerate(routes):
            tooltip = f"Option {i+1}: {route_item['distance']:.1f} km, {route_item['duration']:.1f} min"
            folium.PolyLine(route_item['coords'], color=route_item['color'], weight=route_item['weight'], opacity=0.8, tooltip=tooltip, dash_array='5, 5' if i > 0 else None).add_to(m)
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
        <i style="background:#1E90FF; width:15px; height:15px; display:inline-block;"></i> Itinéraire Principal<br>
        <i style="background:#32CD32; width:15px; height:15px; display:inline-block;"></i> Alternative 1<br>
        <i style="background:#9932CC; width:15px; height:15px; display:inline-block;"></i> Alternative 2<br>
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
    st.write(f"📍 Votre position IP actuelle (utilisée comme point de départ par défaut): **{current_ip_location_name}** (Lat: {current_ip_lat:.4f}, Lon: {current_ip_lon:.4f})")
    st.markdown("</div>", unsafe_allow_html=True)

    if 'last_osrm_start_coords' not in st.session_state: st.session_state.last_osrm_start_coords = None
    if 'last_osrm_dest_coords' not in st.session_state: st.session_state.last_osrm_dest_coords = None
    if 'last_routes_data' not in st.session_state: st.session_state.last_routes_data = None
    if 'last_weather_info' not in st.session_state: st.session_state.last_weather_info = None
    if 'last_severity' not in st.session_state: st.session_state.last_severity = None
    if 'last_speech_text' not in st.session_state: st.session_state.last_speech_text = ""

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
            st.write(f"🌤️ Météo détectée: **{weather_label}** (Confiance: {confidence:.1f}%)")
            risk_message = f"Risque d'accident: {severity_analysis}"
            st.markdown(f"🚨 {risk_message}", unsafe_allow_html=True)
            safety_advice_message = get_safety_advice(severity_analysis)
            st.write(f"⚠️ **Conseil de sécurité:** {safety_advice_message}")
            
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
                dest_location_obj = geolocator.geocode(f"{destination_input}, Tunisia", exactly_one=True, country_codes="tn", timeout=10)
                if not dest_location_obj:
                    dest_location_obj = geolocator.geocode(f"{destination_input}, Tunisia", exactly_one=True, timeout=10)
                if dest_location_obj:
                    st.session_state.last_osrm_dest_coords = (dest_location_obj.latitude, dest_location_obj.longitude)
                    success_msg = f"Destination trouvée: {dest_location_obj.address} à {st.session_state.last_osrm_dest_coords}"
                    st.success(success_msg)
                    
                    # Generate and display audio player for the success message
                    if tts_enabled:
                        audio_player = generate_audio_player(success_msg)
                        st.markdown(audio_player, unsafe_allow_html=True)
                    
                    routes_data = get_routes(st.session_state.last_osrm_start_coords, st.session_state.last_osrm_dest_coords, (app_mode == "Multiple Routes Comparison"))
                    st.session_state.last_routes_data = routes_data
                    if not routes_data:
                        warning_msg = "Aucun itinéraire OSRM trouvé. Une ligne directe sera affichée si possible."
                        st.warning(warning_msg)
                        if tts_enabled:
                            audio_player = generate_audio_player(warning_msg)
                            st.markdown(audio_player, unsafe_allow_html=True)
                else:
                    error_msg = f"Impossible de géocoder la destination: {destination_input}"
                    st.error(error_msg)
                    if tts_enabled:
                        audio_player = generate_audio_player(error_msg)
                        st.markdown(audio_player, unsafe_allow_html=True)
            except Exception as e:
                error_msg = f"Erreur lors de la recherche d'itinéraire ou du géocodage: {str(e)}"
                st.error(error_msg)
                if tts_enabled:
                    audio_player = generate_audio_player(error_msg)
                    st.markdown(audio_player, unsafe_allow_html=True)

    with map_placeholder.container():
        map_to_display = create_map(
            st.session_state.last_osrm_start_coords,
            st.session_state.last_osrm_dest_coords,
            (current_ip_lat, current_ip_lon),
            routes=st.session_state.last_routes_data,
            weather_info=st.session_state.last_weather_info,
            severity=st.session_state.last_severity
        )
        folium_static(map_to_display, width=None, height=600)

if __name__ == "__main__":
    main()