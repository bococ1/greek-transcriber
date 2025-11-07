# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system-level dependencies for PyAV and ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port for Streamlit
EXPOSE 8000

# Streamlit startup
CMD ["streamlit", "run", "ui.py", "--server.port=8000", "--server.address=0.0.0.0"]
