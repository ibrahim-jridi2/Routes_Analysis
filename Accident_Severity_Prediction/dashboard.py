import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import time

# Configuration and CSS (keep your existing CSS)
def load_css():
    st.markdown("""
    <style>
        /* Your existing CSS styles here */
    </style>
    """, unsafe_allow_html=True)

load_css()

# Weather data function (unchanged)
def get_weather_data(lat, lon):
    try:
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Foggy", "Stormy"]
        temperatures = range(15, 35)
        
        weather = {
            "condition": random.choice(weather_conditions),
            "temperature": random.choice(temperatures),
            "humidity": random.randint(30, 90),
            "wind_speed": round(random.uniform(0, 30), 1),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        weather_emojis = {
            "Sunny": "☀️",
            "Cloudy": "☁️",
            "Rainy": "🌧️",
            "Foggy": "🌫️",
            "Stormy": "⛈️"
        }
        
        weather["emoji"] = weather_emojis.get(weather["condition"], "❓")
        return weather
    except Exception as e:
        st.error(f"Weather data error: {str(e)}")
        return None

# Initialize session state
def init_session():
    if 'weather_data' not in st.session_state:
        st.session_state.weather_data = get_weather_data(36.8065, 10.1815)
        st.session_state.last_refresh = time.time()
    if 'latitude' not in st.session_state:
        st.session_state.latitude = 36.8065
    if 'longitude' not in st.session_state:
        st.session_state.longitude = 10.1815

# Weather component with auto-refresh
def weather_component():
    current_time = time.time()
    
    # Check if 5 seconds have passed since last refresh
    if current_time - st.session_state.last_refresh > 5:
        st.session_state.weather_data = get_weather_data(
            st.session_state.latitude, 
            st.session_state.longitude
        )
        st.session_state.last_refresh = current_time
        st.experimental_rerun()
    
    # Display weather data
    if st.session_state.weather_data:
        weather = st.session_state.weather_data
        st.markdown(f"""
        <div class='weather-container'>
            <div class='weather-icon'>{weather['emoji']}</div>
            <div class='weather-info'>
                <div class='weather-temp'>{weather['temperature']}°C</div>
                <div class='weather-desc'>{weather['condition']}</div>
                <div>Humidity: {weather['humidity']}%</div>
                <div>Wind: {weather['wind_speed']} km/h</div>
                <div style='font-size: 0.8rem; color: var(--text-secondary);'>
                    Last update: {weather['timestamp']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Main dashboard function
def dashboard():
    init_session()
    
    st.markdown("<h1 style='text-align: center;'><i class='fas fa-tachometer-alt'></i> Road Safety Dashboard</h1>", 
                unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Weather widget
        st.markdown("<div class='widget-container animate'>", unsafe_allow_html=True)
        st.markdown("<div class='widget-title'><i class='fas fa-cloud-sun'></i> Weather Conditions</div>", 
                    unsafe_allow_html=True)
        weather_component()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Coordinates widget
        st.markdown("<div class='widget-container animate' style='animation-delay: 0.2s;'>", 
                    unsafe_allow_html=True)
        st.markdown("<div class='widget-title'><i class='fas fa-location-dot'></i> Coordinates</div>", 
                    unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='coords-display'>
            Latitude: {st.session_state.latitude:.6f}<br>
            Longitude: {st.session_state.longitude:.6f}
        </div>
        """, unsafe_allow_html=True)
        
        new_lat = st.slider("Latitude", 30.0, 38.0, st.session_state.latitude, 0.001, "%.6f")
        new_lon = st.slider("Longitude", 7.0, 12.0, st.session_state.longitude, 0.001, "%.6f")
        
        if new_lat != st.session_state.latitude or new_lon != st.session_state.longitude:
            st.session_state.latitude = new_lat
            st.session_state.longitude = new_lon
            st.session_state.weather_data = get_weather_data(new_lat, new_lon)
            st.experimental_rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Map widget (unchanged from your original)
        st.markdown("<div class='widget-container animate' style='animation-delay: 0.1s;'>", 
                    unsafe_allow_html=True)
        st.markdown("<div class='widget-title'><i class='fas fa-map'></i> Location Map</div>", 
                    unsafe_allow_html=True)
        
        m = folium.Map(
            location=[st.session_state.latitude, st.session_state.longitude], 
            zoom_start=13, 
            tiles="CartoDB dark_matter"
        )
        folium.Marker(
            [st.session_state.latitude, st.session_state.longitude],
            tooltip="Current location",
            icon=folium.Icon(color="red", icon="location-dot", prefix="fa")
        ).add_to(m)
        folium.Circle(
            [st.session_state.latitude, st.session_state.longitude],
            radius=2000,
            color="#3a86ff",
            fill=True,
            fill_color="#3a86ff",
            fill_opacity=0.2
        ).add_to(m)
        folium_static(m, width=700, height=400)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Rest of your dashboard (tabs, charts, etc.)
    # ... [keep all your existing code for the other components]

# Run the app
if __name__ == "__main__":
    dashboard()