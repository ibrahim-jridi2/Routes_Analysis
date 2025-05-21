FROM python:3.9-slim
WORKDIR /app
# Install essential packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
# Set locale environment variables
ENV LANG en_US.utf8
ENV LC_ALL en_US.UTF-8
ENV PYTHONIOENCODING=utf-8
# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir numpy==1.23.5
RUN pip install --default-timeout=100 --retries=5 --no-cache-dir -r requirements.txt

# Copy encoding fix script and run it
COPY Accident_Severity_Prediction/convert_encoding.py .
RUN python convert_encoding.py

# Copy application files - adjust the COPY command to reflect your directory structure
COPY Accident_Severity_Prediction/ /app/Accident_Severity_Prediction/
# Make sure the Python module can be found
RUN mkdir -p /app/Accident_Severity_Prediction
EXPOSE 8501
# Run the Streamlit app with the main.py entry point
ENTRYPOINT ["streamlit", "run", "Accident_Severity_Prediction/main.py", "--server.port=8501", "--server.address=0.0.0.0"]