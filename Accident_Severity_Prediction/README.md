# Tunisia Road Safety Navigator

A Streamlit application that analyzes road conditions, predicts accident risks, and provides safe navigation routes across Tunisia.

## Features

- **Road Condition Analysis**: Upload images to analyze current weather conditions
- **Accident Risk Prediction**: Based on weather conditions, location, and historical data
- **Safe Navigation**: Find optimal routes with safety information
- **Multiple Route Options**: Compare different routes to your destination
- **Safety Recommendations**: Get driving advice based on predicted risk levels

## Installation

### Requirements

- Python 3.7+
- Tensorflow 2.x
- Streamlit

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/tunisia-road-safety-navigator.git
   cd tunisia-road-safety-navigator
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Download the pre-trained models:
   - `weather_cnn_model.h5`: Weather classification model
   - `accident_severity_model.pkl`: Accident severity prediction model

   Place these files in the root directory.

## Usage

1. Run the Streamlit app:
   ```
   streamlit run tunisia_road_safety_app.py
   ```

2. Open your browser and navigate to `http://localhost:8501`

3. Upload road condition images (optional)

4. Enter your destination in Tunisia

5. Click "Find Routes" to see navigation options with safety information

## Docker Deployment

1. Build the Docker image:
   ```
   docker build -t tunisia-road-safety-app .
   ```

2. Run the container:
   ```
   docker run -p 8501:8501 tunisia-road-safety-app
   ```

3. Access the app at `http://localhost:8501`

## Models

The application uses two pre-trained models:

1. **Weather CNN Model** (`weather_cnn_model.h5`):
   - A convolutional neural network trained to classify weather conditions in images
   - Recognizes: Cloudy, Foggy, Rainy, Shine, Sunrise

2. **Accident Severity Model** (`accident_severity_model.pkl`):
   - A gradient boosting classifier that predicts accident severity
   - Takes into account weather conditions, location, time, and road features
   - Predicts: Medium, High, Critical risk levels

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.