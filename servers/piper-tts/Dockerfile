# Use an appropriate base image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Install dependencies
# Models: https://github.com/rhasspy/piper/blob/master/VOICES.md
RUN \
    git init && \
    git remote add origin https://github.com/rhasspy/piper && \
    git fetch origin 078bf8a17e24ebb18332710354c0797872dcef6a --depth=1 && \
    git reset --hard FETCH_HEAD && \
    cd src/python_run/ && \
    python3 -m pip install -e . && \
    python3 -m pip install -r requirements_http.txt && \
    mkdir -p /app/models/ && \
    cd /app/models/ && \
    wget -O model.onnx https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/low/en_US-lessac-low.onnx?download=true && \
    wget -O model.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/low/en_US-lessac-low.onnx.json?download=true.json

# Expose the port the server will run on
EXPOSE 10803

# Command to run the server
ENTRYPOINT ["python3", "-m", "piper.http_server", "--model", "/app/models/model.onnx", "--config", "/app/models/model.onnx.json", "--port", "10803"]