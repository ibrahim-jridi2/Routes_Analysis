import streamlit as st
import sys
import os

# Configuration de la page
st.set_page_config(
    page_title="Tunisia Road Safety Navigator",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for navigation
if 'page' not in st.session_state:
    st.session_state.page = 'home'

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
        
        /* Logo et titre */
        .app-header {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
            padding: 20px;
            background: linear-gradient(90deg, rgba(58, 134, 255, 0.2), rgba(131, 56, 236, 0.2));
            border-radius: 15px;
            box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.2);
        }
        
        .app-logo {
            font-size: 3rem;
            margin-right: 15px;
            color: var(--accent);
        }
        
        .app-title {
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }
        
        .app-subtitle {
            font-size: 1rem;
            color: var(--text-secondary);
            margin: 5px 0 0 0;
        }
        
        /* Style des cartes de navigation */
        .nav-container {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .nav-card {
            background: linear-gradient(145deg, var(--card-bg), #222222);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.05);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .nav-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px 0 rgba(58, 134, 255, 0.3);
        }
        
        .nav-card.active {
            background: linear-gradient(145deg, var(--primary), var(--secondary));
            box-shadow: 0 8px 25px 0 rgba(58, 134, 255, 0.5);
        }
        
        .nav-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        
        .nav-title {
            font-weight: bold;
            color: var(--text);
            font-family: 'Orbitron', sans-serif;
        }
        
        /* Special styling for full-card buttons */
        .stButton > button {
            width: 100%;
            height: 100%;
            background: transparent;
            border: none;
            color: transparent;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 10;
            cursor: pointer;
        }
        
        /* Style for navigation column that will contain the card and the button */
        .nav-column {
            position: relative;
            min-height: 150px;
        }
        
        /* Animation pour les éléments */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .animate {
            animation: fadeIn 0.5s ease-out forwards;
        }
    </style>
    
    <!-- Ajout de Font Awesome pour les icônes -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    """, unsafe_allow_html=True)

# Charger les styles CSS
load_css()

# Fonction pour afficher l'en-tête de l'application
def show_header():
    st.markdown("""
    <div class="app-header animate">
        <div class="app-logo"><i class="fas fa-road"></i></div>
        <div>
            <h1 class="app-title">Tunisia Road Safety Navigator</h1>
            <p class="app-subtitle">Analysis of road conditions and safe navigation in Tunisia</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Fonction de navigation
def navigate_to(page):
    st.session_state.page = page
    
# Function to create a clickable card that combines HTML and button functionality
def clickable_card(title, icon, is_active, on_click_page, key):
    # Create a unique key for this instance
    container_key = f"{key}_container"
    
    # Use a container to hold both elements
    container = st.container()
    
    # Create the button first
    clicked = st.button(title, key=key)
    
    # Handle the click
    if clicked:
        navigate_to(on_click_page)
        st.experimental_rerun()
    
    # Create the visual card on top with pointer-events set to none
    card_class = "nav-card active" if is_active else "nav-card"
    html = f"""
    <style>
        /* Better button styling */
        .stButton button {{
            width: 100%;
            height: 120px;
            background-color: transparent;
            color: transparent;
            border: none;
            padding: 0;
            position: relative;
        }}
        
        /* Make the button label transparent */
        #{key} {{
            color: transparent !important;
        }}
        
        /* Position the visual card directly on top of the button */
        #{container_key} {{
            margin-top: -120px;
            position: relative;
            z-index: 1000;
            pointer-events: none; /* This lets clicks pass through to the button */
            display: block;
            width: 100%;
            height: 120px;
        }}
    </style>
    
    <div id="{container_key}">
        <div class="{card_class}">
            <div class="nav-icon"><i class="fas fa-{icon}"></i></div>
            <div class="nav-title">{title}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    
    return clicked

# Fonction pour afficher la navigation
def show_navigation():
    current_page = st.session_state.page
    
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
    # Dashboard card
    with col2:
        clickable_card(
            title="Dashboard", 
            icon="tachometer-alt", 
            is_active=(current_page == 'home'),
            on_click_page="home",
            key="home_btn"
        )
    
    # Accident Severity card
    with col3:
        clickable_card(
            title="Accident Severity", 
            icon="route", 
            is_active=(current_page == 'dashboard'),
            on_click_page="dashboard",
            key="dashboard_btn"
        )

# Add debug function to help locate files
def debug_file_locations():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    st.write(f"Current directory: {current_dir}")
    st.write(f"Files in current directory: {os.listdir(current_dir)}")
    
    # Try to find dashboard.py
    possible_locations = [
        current_dir,
        os.path.join(current_dir, ".."),
        "/app",
        "/app/Accident_Severity_Prediction"
    ]
    
    for location in possible_locations:
        try:
            files = os.listdir(location)
            if "dashboard.py" in files:
                st.success(f"Found dashboard.py in {location}")
            else:
                st.warning(f"dashboard.py not found in {location}")
            st.write(f"Files in {location}: {files}")
        except Exception as e:
            st.error(f"Error reading {location}: {str(e)}")

# Fonction principale
def main():
    # Afficher l'en-tête
    show_header()
    
    # Afficher la navigation
    show_navigation()
    
    # Add the current directory to the python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Debug mode - uncomment if needed
    # if st.checkbox("Show debug info"):
    #    debug_file_locations()
    
    # Déterminer quelle page afficher basé sur l'état de session
    page = st.session_state.page
    
    # Importer et afficher la page appropriée
    if page == "dashboard":
        try:
            # Try to import the original app
            try:
                # First try importing from the same directory
                from tunisia_road_safety_app import main as original_app
                original_app()
            except ImportError:
                st.warning("L'application de navigation sera disponible prochainement.")
        except Exception as e:
            st.error(f"Erreur lors du chargement de l'application de navigation: {str(e)}")
            
    elif page == "home":
        try:
            # First, we print the dashboard module directly and execute it
            try:
                # Try to load dashboard module from same directory
                from dashboard import dashboard
                dashboard()
            except ImportError as e:
                # If that fails, try to look for dashboard.py in the current directory and load it directly
                dashboard_path = os.path.join(current_dir, "dashboard.py")
                
                if os.path.exists(dashboard_path):
                    st.info(f"Found dashboard.py at {dashboard_path}. Attempting to load.")
                    
                    # Load dashboard module directly from file
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("dashboard_module", dashboard_path)
                    dashboard_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(dashboard_module)
                    
                    # Call the dashboard function
                    dashboard_module.dashboard()
                else:
                    # As a last resort, execute the dashboard.py content directly
                    st.error(f"Dashboard module could not be imported and dashboard.py not found in {current_dir}.")
                    # Uncomment to see debug info:
                    # debug_file_locations()
        except Exception as e:
            st.error(f"Erreur lors du chargement du tableau de bord: {str(e)}")
            st.error(f"Type d'erreur: {type(e).__name__}")
            # Uncomment for more detailed stack trace:
            # import traceback
            # st.code(traceback.format_exc())
    else:
        st.error("Page non trouvée")

if __name__ == "__main__":
    main()