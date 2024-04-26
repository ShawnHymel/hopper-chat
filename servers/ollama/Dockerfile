# Use an appropriate base image
FROM ollama/ollama:0.1.32

# Set the working directory
WORKDIR /app

# Set the port for the ollama server
ENV OLLAMA_HOST 0.0.0.0:10802

# Expose the port the server will run on
EXPOSE 10802

# Download the model
RUN \
    ollama serve & \
    sleep 5 ; \
    ollama pull llama3:8b ; \
    echo "kill 'ollama serve' process" ; \
    ps -ef | grep 'ollama serve' | grep -v grep | awk '{print $2}' | xargs -r kill -9

# Command to run the server
ENTRYPOINT ["/bin/bash", "-c", "ollama serve & sleep 5 ; ollama run llama3:8b"]