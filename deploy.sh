#!/bin/bash

# Mosquitto MQTT Broker Deployment Script
# For DigitalOcean Droplet 'Enviroscan'

set -e

echo "=========================================="
echo "Mosquitto MQTT Broker Deployment"
echo "=========================================="
echo ""

# Create required directories
echo "Creating required directories..."
mkdir -p data log

# Set proper permissions for Mosquitto
echo "Setting permissions..."
sudo chown -R 1883:1883 data log config

# Pull the latest Mosquitto image
echo "Pulling latest Mosquitto Docker image..."
docker compose pull

# Start the MQTT broker
echo "Starting Mosquitto MQTT broker..."
docker compose up -d

# Wait for container to be ready
echo "Waiting for broker to start..."
sleep 5

# Check if container is running
if docker compose ps | grep -q "Up"; then
    echo ""
    echo "=========================================="
    echo "✓ Mosquitto MQTT Broker is running!"
    echo "=========================================="
    echo ""
    echo "MQTT Port: 1883"
    echo "WebSocket Port: 9001"
    echo ""
    echo "View logs with: docker compose logs -f mosquitto"
    echo "Stop broker with: docker compose down"
    echo ""
    echo "⚠️  WARNING: Anonymous access is enabled!"
    echo "   For production, configure authentication."
    echo ""
else
    echo ""
    echo "❌ Failed to start Mosquitto broker"
    echo "Check logs with: docker compose logs mosquitto"
    exit 1
fi
