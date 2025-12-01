#!/bin/bash

# Enable MQTT Authentication Script
# Updates Mosquitto configuration to require authentication

set -e

echo "=========================================="
echo "Enable MQTT Authentication"
echo "=========================================="
echo ""

# Check if password file exists
if [ ! -f "config/passwd" ]; then
    echo "Error: Password file not found!"
    echo "Please run ./setup_mqtt_auth.sh first"
    exit 1
fi

# Backup original config
if [ ! -f "config/mosquitto.conf.backup" ]; then
    cp config/mosquitto.conf config/mosquitto.conf.backup
    echo "✓ Backed up original configuration to mosquitto.conf.backup"
fi

# Update configuration to enable authentication
cat > config/mosquitto.conf << 'EOF'
# Mosquitto MQTT Broker Configuration
# Authentication Enabled

# Listener configuration
listener 1883
protocol mqtt

# WebSocket listener
listener 9001
protocol websockets

# Authentication
allow_anonymous false
password_file /mosquitto/config/passwd

# Persistence configuration
persistence true
persistence_location /mosquitto/data/

# Logging
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
log_type all

# Connection settings
max_connections -1
EOF

echo "✓ Updated Mosquitto configuration"
echo ""

# Restart Mosquitto to apply changes
echo "Restarting Mosquitto broker..."
docker compose restart mosquitto

echo ""
echo "Waiting for broker to restart..."
sleep 3

# Check if broker is running
if docker compose ps mosquitto | grep -q "Up"; then
    echo ""
    echo "=========================================="
    echo "✓ Authentication Enabled Successfully!"
    echo "=========================================="
    echo ""
    echo "MQTT broker now requires username and password."
    echo ""
    echo "Next steps:"
    echo "1. Update your .env file with bridge credentials"
    echo "2. Restart the bridge service: docker compose restart mqtt-bridge"
    echo "3. Configure CR6 dataloggers with authentication"
    echo ""
else
    echo ""
    echo "❌ Error: Broker failed to restart"
    echo "Check logs: docker compose logs mosquitto"
    echo ""
    echo "To restore original configuration:"
    echo "  cp config/mosquitto.conf.backup config/mosquitto.conf"
    echo "  docker compose restart mosquitto"
    exit 1
fi
