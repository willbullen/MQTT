#!/bin/bash

# Setup Admin User for MQTT Broker
# This script creates an admin user and enables authentication

set -e

echo "=========================================="
echo "MQTT Admin User Setup"
echo "=========================================="
echo ""

# Check if running in MQTT directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: Must run this script from the MQTT directory"
    exit 1
fi

# Create config directory if it doesn't exist
mkdir -p config

echo "Creating admin user..."
echo ""

# Create password file with admin user
# Password: B@ff1ed!2025
docker compose exec mosquitto mosquitto_passwd -c -b /mosquitto/config/passwd admin 'B@ff1ed!2025'

echo "✓ Admin user created successfully"
echo ""
echo "Username: admin"
echo "Password: B@ff1ed!2025"
echo ""

# Backup original config if it exists
if [ -f "config/mosquitto.conf" ] && [ ! -f "config/mosquitto.conf.backup" ]; then
    cp config/mosquitto.conf config/mosquitto.conf.backup
    echo "✓ Backed up original configuration"
fi

# Update Mosquitto configuration to require authentication
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

echo "✓ Updated Mosquitto configuration to require authentication"
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
    echo "✓ Setup Complete!"
    echo "=========================================="
    echo ""
    echo "MQTT Broker: 138.68.158.9:1883"
    echo "Username: admin"
    echo "Password: B@ff1ed!2025"
    echo ""
    echo "Authentication is now REQUIRED for all connections."
    echo ""
    echo "Test with:"
    echo "  mosquitto_pub -h 138.68.158.9 -u admin -P 'B@ff1ed!2025' -t test -m 'Hello'"
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
