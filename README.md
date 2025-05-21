# Tunisia Road Safety Navigator - Application Multi-pages

Cette application Streamlit améliorée intègre l'application originale de navigation routière en Tunisie avec un nouveau tableau de bord futuriste pour la visualisation des données météorologiques, des coordonnées géographiques et des statistiques d'accidents.

## Structure de l'application

L'application est organisée en plusieurs fichiers :

- `main.py` : Point d'entrée principal qui gère la navigation entre les pages
- `dashboard.py` : Nouvelle page de tableau de bord avec widgets interactifs
- `upload/tunisia_road_safety_app.py` : Application originale avec design modernisé

## Fonctionnalités

### Page de Navigation (originale)
- Analyse des conditions météorologiques à partir d'images
- Prédiction des risques d'accidents
- Planification d'itinéraires sécurisés
- Alertes vocales pour la sécurité

### Nouveau Tableau de Bord
- Widget météo avec visualisation par emoji
- Widget de coordonnées géographiques interactif
- Statistiques historiques sur les accidents routiers
- Visualisations interactives (tendances, conditions routières, carte de chaleur)

## Design Futuriste

L'application a été entièrement repensée avec un design futuriste :
- Palette de couleurs sombre avec accents lumineux
- Animations et transitions fluides
- Widgets avec effets de profondeur et dégradés
- Police Orbitron pour un style futuriste
- Interface responsive adaptée à différentes tailles d'écran

## Comment exécuter l'application

1. Assurez-vous que toutes les dépendances sont installées
2. Lancez l'application avec la commande :
   ```
   streamlit run app_multipage/main.py
   ```

## Navigation entre les pages

La navigation entre les pages se fait via la barre de navigation en haut de l'application :
- **Navigation** : Accès à l'application originale de planification d'itinéraires
- **Tableau de Bord** : Accès au nouveau dashboard avec widgets interactifs

## Widgets du Tableau de Bord

### Widget Météo
- Affiche les conditions météorologiques actuelles avec emoji
- Température, humidité et vitesse du vent
- Bouton de rafraîchissement des données

### Widget Coordonnées
- Affichage des coordonnées géographiques actuelles
- Sliders pour ajuster manuellement la latitude et longitude
- Carte interactive montrant la position

### Widget Statistiques
- Tendances mensuelles des accidents et victimes
- Répartition des conditions routières
- Carte de chaleur des accidents
- Résumé des statistiques importantes

## Personnalisation

Vous pouvez personnaliser davantage l'application en modifiant :
- Les styles CSS dans les fonctions `load_css()`
- Les palettes de couleurs dans les variables CSS `:root`
- Les visualisations dans les fonctions de génération de graphiques

## Dépendances

L'application utilise les bibliothèques suivantes :
- Streamlit
- Pandas
- NumPy
- Folium
- Plotly
- TensorFlow
- ONNX Runtime
- gTTS (pour les alertes vocales)
