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

# Set page configuration only if the script is executed directly (not imported)
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
    /* Futuristic color palette */
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
    
    /* General styles */
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
        margin-bottom: 30px;
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
    
    /* Streamlit elements customization */
    .stButton{
        margin-bottom: 30px;
    }
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
    
    /* Animation for elements */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate {
        animation: fadeIn 0.5s ease-out forwards;
    }
    
    /* Add Orbitron font for futuristic style */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&display=swap');
</style>

<!-- Add Font Awesome for icons -->
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

# Define risk weights for each weather condition
weather_risk_weights = {
    'Cloudy': 1.2,    # Cloudy - slightly increased risk
    'Foggy': 2.0,     # Foggy - high risk
    'Rainy': 1.8,     # Rainy - moderately high risk
    'Shine': 1.0,     # Sunny - base risk
    'Sunrise': 1.3,   # Sunrise - reduced visibility
    'Unknown': 1.5    # Unknown - default medium risk
}

# Define risk weights for each accident severity level
severity_risk_weights = {
    'Medium': 1.5,    # Medium risk
    'High': 2.5,      # High risk
    'Critical': 4.0,  # Critical risk
    'Unknown': 2.0    # Unknown - default medium-high risk
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

def evaluate_routes(routes, weather_info, severity):
    if not routes or not weather_info or not severity:
        return 0  # Default to first route if insufficient data
    
    weather_label, weather_confidence = weather_info
    weather_risk = weather_risk_weights.get(weather_label, weather_risk_weights['Unknown'])
    severity_risk = severity_risk_weights.get(severity, severity_risk_weights['Unknown'])
    
    # Calculate a score for each route (lower score is better)
    route_scores = []
    for i, route in enumerate(routes):
        # Base factors: distance and duration
        distance_factor = route['distance'] / 10  # Normalize distance (in km)
        duration_factor = route['duration'] / 60  # Normalize duration (in minutes)
        
        # Risk factor based on weather and accident severity
        risk_factor = weather_risk * severity_risk
        
        # Final score (weighted combination of factors)
        # Higher risk penalizes longer routes more
        score = (distance_factor * 0.3 + duration_factor * 0.2) * risk_factor
        
        route_scores.append((i, score))
    
    # Sort routes by score (lowest to highest)
    route_scores.sort(key=lambda x: x[1])
    
    # Return index of best route
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

    # Use white background by default
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start, tiles="CartoDB positron")
    
    # Add other tile layers as options
    folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(m)
    folium.TileLayer('Stamen Terrain', name='Terrain Map').add_to(m)
    folium.TileLayer('OpenStreetMap', name='Street Map').add_to(m)

    if current_ip_location_coords:
        folium.Marker(
            current_ip_location_coords, 
            tooltip="Your Current IP Location", 
            popup=f"IP Position: {current_ip_location_coords[0]:.4f}, {current_ip_location_coords[1]:.4f}", 
            icon=folium.Icon(color='purple', icon='user', prefix='fa')
        ).add_to(m)

    if start_coords and end_coords:
        start_tooltip = "Route Start"
        if weather_info:
            start_tooltip += f"\nWeather: {weather_info[0]} ({weather_info[1]:.1f}%)"
            start_tooltip += f"\nRisk: {severity}"
        folium.Marker(start_coords, tooltip=start_tooltip, popup=f"Route Start: {start_coords[0]:.4f}, {start_coords[1]:.4f}", icon=folium.Icon(color='green', icon='play')).add_to(m)
        folium.Marker(end_coords, tooltip="Route Destination", popup=f"Route Destination: {end_coords[0]:.4f}, {end_coords[1]:.4f}", icon=folium.Icon(color='red', icon='stop')).add_to(m)

    if routes:
        # Evaluate routes and get index of best route
        best_route_index = evaluate_routes(routes, weather_info, severity)
        
        for i, route_item in enumerate(routes):
            is_best_route = (i == best_route_index)
            
            # Modify appearance of recommended route
            route_color = '#FF006E' if is_best_route else route_item['color']
            route_weight = 7 if is_best_route else route_item['weight']
            route_opacity = 1.0 if is_best_route else 0.8
            
            # Create more informative tooltip
            tooltip = f"{'RECOMMENDED ROUTE: ' if is_best_route else 'Option: '}{route_item['distance']:.1f} km, {route_item['duration']:.1f} min"
            if is_best_route and weather_info and severity:
                tooltip += f"\nConditions: {weather_info[0]}, Risk: {severity}"
            
            # Add route to map
            route_line = folium.PolyLine(
                route_item['coords'], 
                color=route_color, 
                weight=route_weight, 
                opacity=route_opacity, 
                tooltip=tooltip, 
                dash_array='5, 5' if not is_best_route and i > 0 else None
            ).add_to(m)
            
            # Add moving marker for recommended route
            if is_best_route:
                # Add marker at start of route that will be moved
                route_marker_id = f"route_marker_{i}"
                folium.Marker(
                    route_item['coords'][0],
                    tooltip="Your position on the route",
                    icon=folium.Icon(color='blue', icon='car', prefix='fa'),
                    popup="Automatically moving along recommended route"
                ).add_to(m)
                
                # Add script to move marker along route
                route_coords_js = [[lat, lng] for lat, lng in route_item['coords']]
                js_code = f"""
                <script>
                // Function to move marker along route
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
                        setTimeout(moveMarker, 300);  // Movement speed
                    }}
                }}
                
                // Start movement after 2 seconds
                setTimeout(moveMarker, 2000);
                </script>
                """
                m.get_root().html.add_child(folium.Element(js_code))
    elif start_coords and end_coords:
        folium.PolyLine([start_coords, end_coords], color='gray', weight=3, opacity=0.8, dash_array='5, 5', tooltip="Direct line (no OSRM route found)").add_to(m)
    
    legend_html = '''
    <div style="position: relative; bottom: 50px; left: 50px; width: 220px;
                border:2px solid rgba(255, 255, 255, 0.1); z-index:9999; font-size:14px;
                background-color:rgba(26, 26, 26, 0.8); padding: 10px; border-radius: 10px;
                box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.37);">
        <b style="color: #3a86ff;">Legend</b><br>
        <i class="fa fa-user" style="color:#8338ec; font-size:15px;"></i> Your IP Location<br>
        <i class="fa fa-play" style="color:#06d6a0; font-size:15px;"></i> Route Start<br>
        <i class="fa fa-stop" style="color:#ef476f; font-size:15px;"></i> Route Destination<br>
        <i class="fa fa-car" style="color:#3a86ff; font-size:15px;"></i> Position on Route<br>
        <i style="background:#FF006E; width:15px; height:15px; display:inline-block;"></i> Recommended Route<br>
        <i style="background:#1E90FF; width:15px; height:15px; display:inline-block;"></i> Alternative Route 1<br>
        <i style="background:#32CD32; width:15px; height:15px; display:inline-block;"></i> Alternative Route 2<br>
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
    
    # Determine dominant weather class
    if weather_classes:
        try:
            dominant_class = mode(weather_classes)
            dominant_label = weather_labels_mapping.get(dominant_class, "Unknown")
            avg_confidence = sum(weather_confidences) / len(weather_confidences)
            return dominant_label, dominant_class, avg_confidence
        except:
            # If mode() fails (e.g., multiple modes), take first class
            return weather_labels[0], weather_classes[0], weather_confidences[0]
    return "Unknown", 0, 0

def get_safety_advice(severity):
    if severity == "Critical":
        return "Very dangerous conditions. Avoid driving if possible or exercise extreme caution."
    elif severity == "High":
        return "High accident risk. Drive slowly and maintain increased safety distance."
    elif severity == "Medium":
        return "Moderately risky conditions. Stay alert and respect speed limits."
    else:
        return "Unknown conditions. Drive carefully."

def generate_audio_player(text):
    try:
        # Create temporary file for audio
        temp_dir = tempfile.gettempdir()
        audio_file = os.path.join(temp_dir, f"audio_{uuid.uuid4()}.mp3")
        
        # Generate audio with gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(audio_file)
        
        # Read audio file and encode in base64
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()
        
        # Create HTML audio player
        audio_player = f"""
        <div class="audio-container">
            <audio controls autoplay style="width: 100%;">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">Automatic voice message</div>
        </div>
        """
        
        # Delete temporary file
        os.remove(audio_file)
        
        return audio_player
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")
        return ""

def main():
    # Initialize session variables
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
    
    # Get current IP location
    current_ip_lat, current_ip_lon, current_ip_location_name = get_current_location_cached()
    
    # Main container with animation
    st.markdown("<div class='animate'>", unsafe_allow_html=True)
    
    # Weather conditions analysis section
    st.markdown("<h2 class=\"sub-header\"><i class=\"fas fa-cloud-sun\"></i> Weather Conditions Analysis</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.write("""<div><i class="fa fa-map-marker" style="color: red;"></i> Your location here :</div> **{}** (Lat: {:.4f}, Lon: {:.4f})""".format(
            current_ip_location_name, current_ip_lat, current_ip_lon
        ), unsafe_allow_html=True)
        
        uploaded_images = st.file_uploader("Upload images of current weather conditions", 
                                         type=["jpg", "jpeg", "png"], 
                                         accept_multiple_files=True)
        
        if uploaded_images:
            with st.spinner("Analyzing images..."):
                weather_label, weather_class, weather_confidence = analyze_multiple_images(uploaded_images)
                st.session_state.last_weather_info = (weather_label, weather_confidence)
                
                # Predict accident severity
                severity = predict_accident_severity(weather_class, (current_ip_lat, current_ip_lon))
                st.session_state.last_severity = severity
                
                st.write(f"""<div><i class="fa-solid fa-cloud"></i> Detected weather conditions: **{weather_label}** (Confidence: {weather_confidence:.1f}%)</div> """, unsafe_allow_html=True)
                st.write(f"""<div><i class="fa-solid fa-circle-exclamation" style="color: red;"></i> Predicted accident risk level: <span class='{risk_color_mapping.get(severity, '')}'>{severity}</span></div>  """, unsafe_allow_html=True)
                st.write(f"""<div><i class="fa-solid fa-lightbulb" style="color: yellow;"></i>**{get_safety_advice(severity)}**</div> """, unsafe_allow_html=True)
                
                # Generate audio message for voice alerts
                if tts_enabled:
                    safety_speech = f"Road safety alert. Detected weather conditions: {weather_label}. Accident risk level: {severity}. {get_safety_advice(severity)}"
                    safety_audio = generate_audio_player(safety_speech)
                    st.markdown(safety_audio, unsafe_allow_html=True)
        else:
            st.info("Please upload images of current weather conditions for analysis.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        if uploaded_images:
            st.write("### Analyzed Images")
            image_cols = st.columns(min(3, len(uploaded_images)))
            for i, img_file in enumerate(uploaded_images):
                with image_cols[i % 3]:
                    st.image(img_file, caption=f"Image {i+1}", use_column_width=True)
        else:
            st.markdown("""
            ### How It Works
            
            1. **Upload images** of current weather conditions
            2. Our **AI will analyze** visible weather conditions
            3. The system **predicts accident risk level** based on conditions
            4. You'll receive **tailored safety advice**
            
            For best results, upload multiple images taken outdoors clearly showing sky and road conditions.
            """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Route planning section
    st.markdown("<h2 class=\"sub-header\"><i class=\"fas fa-route\"></i> Safe Route Planning</h2>", unsafe_allow_html=True)
    
    # Create a container for the destination input that won't be overlapped by the map
    with st.container():
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        destination_input = st.text_input("Enter your destination in Tunisia", "Hammamet, Tunisia")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Create a separate container for the map with some top margin
    with st.container():
        st.markdown("<div style='margin-top:60px;'>", unsafe_allow_html=True)
        
        if st.button("Find Routes", key="find_routes_btn"):
            st.session_state.last_osrm_start_coords = (current_ip_lat, current_ip_lon)
            st.session_state.last_routes_data = None
            st.session_state.last_osrm_dest_coords = None
            with st.spinner("Finding routes..."):
                geolocator = Nominatim(user_agent="tunisia_road_safety_app_gtts_v1")
                try:
                    dest_location_obj = geolocator.geocode(f"{destination_input}, Tunisia")
                    if dest_location_obj:
                        dest_lat, dest_lon = dest_location_obj.latitude, dest_location_obj.longitude
                        st.session_state.last_osrm_dest_coords = (dest_lat, dest_lon)
                        routes_data = get_routes(st.session_state.last_osrm_start_coords, st.session_state.last_osrm_dest_coords)
                        st.session_state.last_routes_data = routes_data
                        
                        # Evaluate routes and get index of best route
                        if routes_data and st.session_state.last_weather_info and st.session_state.last_severity:
                            best_route_index = evaluate_routes(routes_data, st.session_state.last_weather_info, st.session_state.last_severity)
                            st.session_state.best_route_index = best_route_index
                        
                        if routes_data:
                            # Create map with white background
                            m = create_map(
                                st.session_state.last_osrm_start_coords, 
                                st.session_state.last_osrm_dest_coords, 
                                (current_ip_lat, current_ip_lon), 
                                routes_data, 
                                st.session_state.last_weather_info, 
                                st.session_state.last_severity
                            )
                            folium_static(m, width=1200, height=600)
                            
                            # Display route details with highlighting of best route
                            st.markdown("<h3 class=\"sub-header\">Route Details</h3>", unsafe_allow_html=True)
                            
                            for i, route in enumerate(routes_data):
                                is_best_route = (i == st.session_state.best_route_index)
                                route_class = "recommended-route" if is_best_route else ""
                                
                                st.markdown(f"<div class='{route_class}'>", unsafe_allow_html=True)
                                route_title = f"{'[RECOMMENDED] RECOMMENDED ROUTE' if is_best_route else f'Option {i+1}'}"
                                st.markdown(f"### {route_title}")
                                st.write(f"<span class='icon-road'>[DISTANCE]</span> Distance: **{route['distance']:.1f} km**", unsafe_allow_html=True)
                                st.write(f"<span class='icon-time'>[DURATION]</span> Estimated duration: **{route['duration']:.1f} minutes**", unsafe_allow_html=True)
                                
                                if is_best_route and st.session_state.last_weather_info and st.session_state.last_severity:
                                    weather_label, confidence = st.session_state.last_weather_info
                                    st.write(f"<span class='icon-weather'>[WEATHER]</span> Weather conditions: **{weather_label}** (Confidence: {confidence:.1f}%)", unsafe_allow_html=True)
                                    st.write(f"<span class='icon-risk'>[RISK]</span> Risk level: **{st.session_state.last_severity}**", unsafe_allow_html=True)
                                    st.write(f"<span class='icon-warning'>[ADVICE]</span> **Advice:** {get_safety_advice(st.session_state.last_severity)}", unsafe_allow_html=True)
                                    
                                    # Generate audio message for recommended route
                                    if is_best_route:
                                        route_speech = f"Recommended route found. Distance: {route['distance']:.1f} kilometers. Estimated duration: {route['duration']:.1f} minutes. Weather conditions: {weather_label}. {get_safety_advice(st.session_state.last_severity)}"
                                        route_audio = generate_audio_player(route_speech)
                                        st.markdown(route_audio, unsafe_allow_html=True)
                                
                                st.markdown("</div>", unsafe_allow_html=True)
                                st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Explanation of route selection logic
                            st.markdown("<div class=\"info-box\">", unsafe_allow_html=True)
                            st.markdown("<h3><span class='icon-brain'>[LOGIC]</span> Route Selection Logic</h3>", unsafe_allow_html=True)
                            st.write("""
                            The recommended route is selected based on several factors:
                            - **Distance and duration** of the trip
                            - Current **weather conditions** (higher risk: fog, rain)
                            - Predicted **accident risk level** for the area
                            
                            Our algorithm calculates a risk score for each route and recommends the one that offers the best balance between safety and efficiency.
                            """)
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.error("Could not find routes to this destination. Please try another destination.")
                    else:
                        st.error(f"Could not find location: {destination_input}, Tunisia")
                except Exception as e:
                    st.error(f"Error finding routes: {str(e)}")
        
        # Display map with previous data if available
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
            # Display map centered on current IP location
            m = create_map(None, None, (current_ip_lat, current_ip_lon))
            folium_static(m, width=1200, height=600)
        
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # Close main container with animation

if __name__ == "__main__":
    main()