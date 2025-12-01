#!/bin/bash

# MQTT Authentication Setup Script
# This script configures secure authentication for the Mosquitto MQTT broker

set -e

echo "=========================================="
echo "MQTT Authentication Setup"
echo "=========================================="
echo ""

# Check if running in MQTT directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: Must run this script from the MQTT directory"
    exit 1
fi

# Create password file directory if it doesn't exist
mkdir -p config

echo "This script will create usernames and passwords for MQTT access."
echo ""
echo "You will create accounts for:"
echo "  1. CR6 dataloggers (for publishing sensor data)"
echo "  2. MQTT bridge service (for subscribing to data)"
echo "  3. Admin user (for monitoring and management)"
echo ""

# Function to create a user
create_user() {
    local username=$1
    local description=$2
    
    echo "----------------------------------------"
    echo "Creating user: $username"
    echo "Purpose: $description"
    echo "----------------------------------------"
    
    # Use docker compose exec to run mosquitto_passwd inside the container
    if [ -f "config/passwd" ]; then
        # Add to existing file
        docker compose exec mosquitto mosquitto_passwd -b /mosquitto/config/passwd "$username" "$3"
    else
        # Create new file
        docker compose exec mosquitto mosquitto_passwd -c -b /mosquitto/config/passwd "$username" "$3"
    fi
    
    echo "✓ User '$username' created successfully"
    echo ""
}

# Generate secure random passwords
echo "Generating secure passwords..."
echo ""

# Generate passwords (you can change these)
CR6_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
BRIDGE_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
ADMIN_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)

# Create users
create_user "cr6_datalogger" "For CR6 dataloggers to publish data" "$CR6_PASSWORD"
create_user "mqtt_bridge" "For the bridge service to subscribe to topics" "$BRIDGE_PASSWORD"
create_user "admin" "For administrative access and monitoring" "$ADMIN_PASSWORD"

# Save credentials to a secure file
CRED_FILE="mqtt_credentials.txt"
cat > "$CRED_FILE" << EOF
========================================
MQTT Broker Credentials
Generated: $(date)
========================================

MQTT Broker: 138.68.158.9:1883

1. CR6 Datalogger Account
   Username: cr6_datalogger
   Password: $CR6_PASSWORD
   Purpose: Configure this in your CR6 Device Configuration Utility

2. MQTT Bridge Service Account
   Username: mqtt_bridge
   Password: $BRIDGE_PASSWORD
   Purpose: Update this in your .env file

3. Admin Account
   Username: admin
   Password: $ADMIN_PASSWORD
   Purpose: For monitoring and testing

========================================
IMPORTANT: Store these credentials securely!
Delete this file after saving the passwords.
========================================
EOF

echo "=========================================="
echo "✓ MQTT Authentication Configured!"
echo "=========================================="
echo ""
echo "Credentials have been saved to: $CRED_FILE"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo ""
echo "1. View and save your credentials:"
echo "   cat $CRED_FILE"
echo ""
echo "2. Update Mosquitto configuration:"
echo "   Run: ./enable_mqtt_auth.sh"
echo ""
echo "3. Update your .env file with the bridge credentials"
echo ""
echo "4. Configure your CR6 dataloggers with the cr6_datalogger credentials"
echo ""
echo "5. Delete the credentials file after saving:"
echo "   rm $CRED_FILE"
echo ""
