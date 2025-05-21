import streamlit as st
import sys
import os

# Configuration de la page
st.set_page_config(
    page_title="Tunisia Road Safety Navigator",
    page_icon="???",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        
        /* Navigation */
        .nav-container {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            padding: 10px;
        }
        
        .nav-item {
            background: linear-gradient(145deg, var(--card-bg), #222222);
            border-radius: 15px;
            padding: 15px 30px;
            margin: 0 10px;
            text-align: center;
            box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.3s ease;
        }
        
        .nav-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px 0 rgba(58, 134, 255, 0.3);
        }
        
        .nav-item.active {
            background: linear-gradient(145deg, var(--primary), var(--secondary));
            box-shadow: 0 8px 25px 0 rgba(58, 134, 255, 0.5);
        }
        
        .nav-item i {
            font-size: 1.5rem;
            margin-bottom: 8px;
            display: block;
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
        
        /* Style pour les boutons Streamlit par-dessus nos éléments de navigation personnalisés */
        div.stButton > button {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: transparent;
            border: none;
            color: transparent;
            z-index: 10;
        }
        
        div.stButton > button:hover {
            background: transparent;
            border: none;
        }
        
        div.stButton > button:focus {
            box-shadow: none;
        }
        
        /* Pour les conteneurs des boutons */
        div.element-container:has(div.stButton > button) {
            position: relative;
            margin-top: -80px;  /* Ajuster pour aligner avec le nav-item */
            z-index: 20;
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

# Fonction pour afficher la navigation avec des boutons Streamlit au lieu de JavaScript
def show_navigation():
    # Obtenir la page actuelle
    query_params = st.experimental_get_query_params()
    current_page = query_params.get("page", ["home"])[0]
    
    # Créer un conteneur pour la navigation
    nav_cols = st.columns([1, 2, 2, 1])
    
    # Afficher les éléments de navigation sous forme de conteneurs HTML avec des styles
    with nav_cols[1]:
        # Navigation - Home
        is_home_active = current_page == "home"
        home_class = "nav-item active" if is_home_active else "nav-item"
        
        st.markdown(f"""
        <div class="{home_class}" style="cursor: pointer;" id="nav-home">
            <i class="fas fa-tachometer-alt"></i>
            <span>Dashboard</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Bouton invisible par dessus pour capter le clic
        if st.button("Dashboard", key="nav_home_btn", help="Aller au tableau de bord", 
                   use_container_width=True, type="primary" if is_home_active else "secondary"):
            st.experimental_set_query_params(page="home")
            st.experimental_rerun()
    
    with nav_cols[2]:
        # Navigation - Dashboard
        is_dashboard_active = current_page == "dashboard"
        dashboard_class = "nav-item active" if is_dashboard_active else "nav-item"
        
        st.markdown(f"""
        <div class="{dashboard_class}" style="cursor: pointer;" id="nav-dashboard">
            <i class="fas fa-route"></i>
            <span>Accident Severity</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Bouton invisible par dessus pour capter le clic
        if st.button("Accident Severity", key="nav_dashboard_btn", help="Aller à la page de navigation", 
                   use_container_width=True, type="primary" if is_dashboard_active else "secondary"):
            st.experimental_set_query_params(page="dashboard")
            st.experimental_rerun()

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
    
    # Déterminer quelle page afficher
    query_params = st.experimental_get_query_params()
    page = query_params.get("page", ["home"])[0]
    
    # Add the current directory to the python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Debug mode - uncomment if needed
    # if st.checkbox("Show debug info"):
    #    debug_file_locations()
    
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