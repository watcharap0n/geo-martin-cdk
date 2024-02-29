# Use the official image as a parent image
FROM ghcr.io/maplibre/martin

# Set the working directory
WORKDIR /app

# Copy the config file into the Docker image
COPY config.yaml /config/config.yaml

# Run the application
CMD ["--config", "/config/config.yaml"]