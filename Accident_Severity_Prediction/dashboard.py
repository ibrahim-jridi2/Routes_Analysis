import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import random
from PIL import Image
import io
import base64
import time
from datetime import datetime

# Configuration de la page

# Styles CSS pour le design futuriste
def load_css():
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
        
        /* Widgets personnalisés */
        .widget-container {
            background: linear-gradient(145deg, var(--card-bg), #222222);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            transition: all 0.3s ease;
        }
        
        .widget-container:hover {
            box-shadow: 0 8px 32px 0 rgba(58, 134, 255, 0.2);
            transform: translateY(-5px);
        }
        
        .widget-title {
            color: var(--primary);
            font-size: 1.5rem;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            font-family: 'Orbitron', sans-serif;
        }
        
        .widget-title i {
            margin-right: 10px;
            color: var(--accent);
        }
        
        /* Météo widget */
        .weather-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .weather-icon {
            font-size: 4rem;
            margin-right: 20px;
            color: var(--primary);
        }
        
        .weather-info {
            flex-grow: 1;
        }
        
        .weather-temp {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--text);
        }
        
        .weather-desc {
            font-size: 1.2rem;
            color: var(--text-secondary);
        }
        
        /* Coordonnées widget */
        .coords-display {
            font-family: 'Courier New', monospace;
            font-size: 1.2rem;
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 5px;
            border-left: 3px solid var(--accent);
        }
        
        /* Statistiques widget */
        .stat-card {
            background: linear-gradient(145deg, #222222, #333333);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary);
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        /* Animation pour les éléments */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .animate {
            animation: fadeIn 0.5s ease-out forwards;
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
        
        /* Ajout de la police Orbitron pour le style futuriste */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&display=swap');
    </style>
    
    <!-- Ajout de Font Awesome pour les icônes -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    """, unsafe_allow_html=True)

# Charger les styles CSS
load_css()

# Fonction pour obtenir les données météo
def get_weather_data(lat, lon):
    try:
        # Simuler une requête API météo
        weather_conditions = ["Ensoleillé", "Nuageux", "Pluvieux", "Brumeux", "Orageux"]
        temperatures = range(15, 35)
        
        weather = {
            "condition": random.choice(weather_conditions),
            "temperature": random.choice(temperatures),
            "humidity": random.randint(30, 90),
            "wind_speed": round(random.uniform(0, 30), 1),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        # Associer des emojis aux conditions météo
        weather_emojis = {
            "Ensoleillé": "☀️",
            "Nuageux": "☁️",
            "Pluvieux": "🌧️",
            "Brumeux": "🌫️",
            "Orageux": "⛈️"
        }
        
        weather["emoji"] = weather_emojis.get(weather["condition"], "❓")
        
        return weather
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données météo: {str(e)}")
        return None

# Fonction pour générer des données historiques d'accidents
def generate_accident_history():
    # Générer des données pour les 12 derniers mois
    today = datetime.now()
    months = [(today - timedelta(days=30*i)).strftime("%b") for i in range(12)]
    months.reverse()  # Pour avoir l'ordre chronologique
    
    # Données simulées d'accidents
    accidents_data = {
        "date": months,
        "accidents": [random.randint(50, 200) for _ in range(12)],
        "casualties": [random.randint(10, 80) for _ in range(12)],
        "severe_conditions": [random.randint(5, 40) for _ in range(12)]
    }
    
    return pd.DataFrame(accidents_data)

# Fonction pour générer des données de conditions routières
def generate_road_conditions():
    conditions = ["Excellente", "Bonne", "Moyenne", "Mauvaise", "Dangereuse"]
    percentages = [random.randint(5, 30) for _ in range(5)]
    
    # Normaliser pour que la somme soit 100%
    total = sum(percentages)
    normalized = [int(p * 100 / total) for p in percentages]
    
    # Ajuster pour que la somme soit exactement 100%
    diff = 100 - sum(normalized)
    normalized[0] += diff
    
    return pd.DataFrame({
        "condition": conditions,
        "percentage": normalized
    })

# Fonction pour créer une carte avec la position actuelle
def create_location_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB dark_matter")
    
    # Ajouter un marqueur pour la position actuelle
    folium.Marker(
        [lat, lon],
        tooltip="Position actuelle",
        icon=folium.Icon(color="red", icon="location-dot", prefix="fa")
    ).add_to(m)
    
    # Ajouter un cercle autour de la position
    folium.Circle(
        [lat, lon],
        radius=2000,  # 2km de rayon
        color="#3a86ff",
        fill=True,
        fill_color="#3a86ff",
        fill_opacity=0.2
    ).add_to(m)
    
    return m

# Fonction principale du dashboard
def dashboard():
    st.markdown("<h1 style='text-align: center;'><i class='fas fa-tachometer-alt'></i> Road Safety Dashboard</h1>", unsafe_allow_html=True)
    
    # Initialiser les coordonnées par défaut (Tunis)
    if 'latitude' not in st.session_state:
        st.session_state.latitude = 36.8065
    if 'longitude' not in st.session_state:
        st.session_state.longitude = 10.1815
    
    # Initialize weather data and refresh timer
    current_time = datetime.now()
    if 'last_weather_refresh' not in st.session_state:
        st.session_state.last_weather_refresh = current_time
        st.session_state.weather_data = get_weather_data(st.session_state.latitude, st.session_state.longitude)
    
    # Check if 5 seconds have passed since last refresh
    elif (current_time - st.session_state.last_weather_refresh).total_seconds() > 5:
        st.session_state.last_weather_refresh = current_time
        st.session_state.weather_data = get_weather_data(st.session_state.latitude, st.session_state.longitude)
        st.experimental_rerun()
    
    # Disposition en colonnes
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Widget Météo
        st.markdown("<div class='widget-container animate'>", unsafe_allow_html=True)
        st.markdown("<div class='widget-title'><i class='fas fa-cloud-sun'></i> Weather Conditions</div>", unsafe_allow_html=True)
        
        if st.session_state.weather_data:
            st.markdown(f"""
            <div class='weather-container'>
                <div class='weather-icon'>{st.session_state.weather_data['emoji']}</div>
                <div class='weather-info'>
                    <div class='weather-temp'>{st.session_state.weather_data['temperature']}°C</div>
                    <div class='weather-desc'>{st.session_state.weather_data['condition']}</div>
                    <div>Humidity: {st.session_state.weather_data['humidity']}%</div>
                    <div>Winds: {st.session_state.weather_data['wind_speed']} km/h</div>
                    <div style='font-size: 0.8rem; color: var(--text-secondary);'>update: {st.session_state.weather_data['timestamp']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Impossible de récupérer les données météo")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Widget Coordonnées
        st.markdown("<div class='widget-container animate' style='animation-delay: 0.2s;'>", unsafe_allow_html=True)
        st.markdown("<div class='widget-title'><i class='fas fa-location-dot'></i> Geographical Coordinates</div>", unsafe_allow_html=True)
        
        # Affichage des coordonnées actuelles
        st.markdown(f"""
        <div class='coords-display'>
            Latitude: {st.session_state.latitude:.6f}<br>
            Longitude: {st.session_state.longitude:.6f}
        </div>
        """, unsafe_allow_html=True)
        
        # Sliders pour ajuster les coordonnées
        st.markdown("<p>Adjust the coordinates:</p>", unsafe_allow_html=True)
        new_lat = st.slider("Latitude", min_value=30.0, max_value=38.0, value=st.session_state.latitude, step=0.001, format="%.6f")
        new_lon = st.slider("Longitude", min_value=7.0, max_value=12.0, value=st.session_state.longitude, step=0.001, format="%.6f")
        
        # Mettre à jour les coordonnées si elles ont changé
        if new_lat != st.session_state.latitude or new_lon != st.session_state.longitude:
            st.session_state.latitude = new_lat
            st.session_state.longitude = new_lon
            st.experimental_rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Carte de localisation
        st.markdown("<div class='widget-container animate' style='animation-delay: 0.1s;'>", unsafe_allow_html=True)
        st.markdown("<div class='widget-title'><i class='fas fa-map'></i> Location Map</div>", unsafe_allow_html=True)
        
        location_map = create_location_map(st.session_state.latitude, st.session_state.longitude)
        folium_static(location_map, width=700, height=400)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Statistiques historiques (pleine largeur)
    st.markdown("<div class='widget-container animate' style='animation-delay: 0.3s;'>", unsafe_allow_html=True)
    st.markdown("<div class='widget-title'><i class='fas fa-chart-line'></i> Historical Statistics of Accidents</div>", unsafe_allow_html=True)
    
    # Onglets pour différentes visualisations
    tab1, tab2, tab3 = st.tabs(["Monthly trends", "Road conditions", "heat map"])
    
    with tab1:
        # Graphique des tendances mensuelles
        accident_data = generate_accident_history()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=accident_data['date'],
            y=accident_data['accidents'],
            mode='lines+markers',
            name='Accidents',
            line=dict(color='#3a86ff', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=accident_data['date'],
            y=accident_data['casualties'],
            mode='lines+markers',
            name='Victimes',
            line=dict(color='#ff006e', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=accident_data['date'],
            y=accident_data['severe_conditions'],
            mode='lines+markers',
            name='Conditions sévères',
            line=dict(color='#ffbe0b', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Trends in road accidents (last 12 months)",
            xaxis_title="Mois",
            yaxis_title="Nombre",
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Graphique des conditions routières
        road_data = generate_road_conditions()
        
        fig = go.Figure(data=[go.Pie(
            labels=road_data['condition'],
            values=road_data['percentage'],
            hole=.4,
            marker_colors=['#06d6a0', '#3a86ff', '#ffbe0b', '#ff006e', '#ef476f']
        )])
        
        fig.update_layout(
            title="Distribution of road conditions",
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            annotations=[dict(text='Road<br>conditions', x=0.5, y=0.5, font_size=15, showarrow=False)]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Carte de chaleur des accidents
        st.markdown("### Carte de chaleur des accidents routiers")
        
        # Générer des points aléatoires autour de la position actuelle
        num_points = 100
        np.random.seed(42)  # Pour la reproductibilité
        
        # Générer des coordonnées aléatoires dans un rayon de ~10km
        lats = st.session_state.latitude + np.random.normal(0, 0.05, num_points)
        lons = st.session_state.longitude + np.random.normal(0, 0.05, num_points)
        
        # Générer des valeurs d'intensité (nombre d'accidents)
        intensities = np.random.randint(1, 10, num_points)
        
        # Créer un DataFrame
        heatmap_data = pd.DataFrame({
            'lat': lats,
            'lon': lons,
            'intensity': intensities
        })
        
        # Créer la carte de chaleur
        heat_map = folium.Map(location=[st.session_state.latitude, st.session_state.longitude], 
                             zoom_start=11, 
                             tiles="CartoDB dark_matter")
        
        # Ajouter les points de chaleur
        heat_data = [[row['lat'], row['lon'], row['intensity']] for index, row in heatmap_data.iterrows()]
        folium.plugins.HeatMap(heat_data, radius=15, gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}).add_to(heat_map)
        
        # Ajouter un marqueur pour la position actuelle
        folium.Marker(
            [st.session_state.latitude, st.session_state.longitude],
            tooltip="Position actuelle",
            icon=folium.Icon(color="red", icon="location-dot", prefix="fa")
        ).add_to(heat_map)
        
        folium_static(heat_map, width=1000, height=500)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Résumé des statistiques
    st.markdown("<div class='widget-container animate' style='animation-delay: 0.4s;'>", unsafe_allow_html=True)
    st.markdown("<div class='widget-title'><i class='fas fa-info-circle'></i> Summary of Statistics</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-value'>157</div>
            <div class='stat-label'>Accidents this month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-value'>42</div>
            <div class='stat-label'>Victims this month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-value'>-12%</div>
            <div class='stat-label'>Evolution compared to the previous month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-value'>28%</div>
            <div class='stat-label'>Accidents related to weather conditions</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Exécuter le dashboard
if __name__ == "__main__":
    dashboard()