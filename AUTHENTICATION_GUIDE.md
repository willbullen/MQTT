# MQTT Authentication Setup Guide

**Date**: December 1, 2025
**Purpose**: Secure your MQTT broker with username/password authentication

---

## Overview

By default, your Mosquitto MQTT broker allows anonymous connections, which is insecure for production use. This guide will help you enable authentication to protect your system.

## What You'll Accomplish

After following this guide, your MQTT broker will:
- ✅ Require username and password for all connections
- ✅ Have separate accounts for CR6 dataloggers, bridge service, and admin access
- ✅ Use strong, randomly-generated passwords
- ✅ Block unauthorized access attempts

## Prerequisites

- SSH access to your Enviroscan droplet (138.68.158.9)
- The MQTT broker must be running (`docker compose ps` should show mosquitto as "Up")

---

## Step-by-Step Setup

### Step 1: Connect to Your Droplet

```bash
ssh root@138.68.158.9
cd /root/MQTT
```

### Step 2: Create User Accounts

Run the authentication setup script:

```bash
./setup_mqtt_auth.sh
```

This script will:
1. Generate three secure random passwords
2. Create three user accounts:
   - `cr6_datalogger` - For your CR6 devices
   - `mqtt_bridge` - For the bridge service
   - `admin` - For monitoring and testing
3. Save the credentials to `mqtt_credentials.txt`

### Step 3: Save Your Credentials

**IMPORTANT**: View and save these credentials immediately:

```bash
cat mqtt_credentials.txt
```

Copy the output and store it in a secure password manager. You'll need these credentials to configure your CR6 dataloggers and update the bridge service.

**Example output:**
```
========================================
MQTT Broker Credentials
Generated: 2025-12-01 15:30:00
========================================

MQTT Broker: 138.68.158.9:1883

1. CR6 Datalogger Account
   Username: cr6_datalogger
   Password: AbCd1234EfGh5678
   Purpose: Configure this in your CR6 Device Configuration Utility

2. MQTT Bridge Service Account
   Username: mqtt_bridge
   Password: XyZ9876WvUt5432Q
   Purpose: Update this in your .env file

3. Admin Account
   Username: admin
   Password: MnOp2468QrSt1357
   Purpose: For monitoring and testing
```

### Step 4: Enable Authentication

Run the script to update Mosquitto configuration:

```bash
./enable_mqtt_auth.sh
```

This will:
1. Backup your current configuration
2. Update `mosquitto.conf` to require authentication
3. Restart the Mosquitto broker
4. Verify the broker is running correctly

### Step 5: Update Bridge Service Configuration

Edit your `.env` file to add the bridge credentials:

```bash
nano .env
```

Add these lines (use the password from your `mqtt_credentials.txt`):

```ini
# MQTT Authentication
MQTT_USERNAME=mqtt_bridge
MQTT_PASSWORD=XyZ9876WvUt5432Q  # Replace with your actual password
```

Save the file (Ctrl+X, then Y, then Enter).

### Step 6: Restart Bridge Service

```bash
docker compose restart mqtt-bridge
```

### Step 7: Delete Credentials File

After you've saved the credentials securely, delete the file:

```bash
rm mqtt_credentials.txt
```

---

## Configuring Your CR6 Dataloggers

Now that authentication is enabled, you must update your CR6 dataloggers to use the credentials.

### In Device Configuration Utility:

1. Connect to your CR6
2. Go to **Settings Editor** → **MQTT** tab
3. Update these settings:
   - **MQTT Username**: `cr6_datalogger`
   - **MQTT Password**: `[Your cr6_datalogger password]`
4. Click **Apply**
5. Verify connection in the **MQTT State** field

### In Your CRBasic Program:

No changes needed - the username/password are configured in the device settings, not in the program.

---

## Testing Authentication

### Test 1: Verify Anonymous Access is Blocked

Try to publish without credentials (should fail):

```bash
mosquitto_pub -h 138.68.158.9 -t "test/topic" -m "test"
```

**Expected result**: Connection refused or authentication error.

### Test 2: Verify Authenticated Access Works

Try to publish with credentials (should succeed):

```bash
mosquitto_pub -h 138.68.158.9 -u admin -P [your_admin_password] -t "test/topic" -m "test"
```

**Expected result**: Message published successfully.

### Test 3: Subscribe with Credentials

```bash
mosquitto_sub -h 138.68.158.9 -u admin -P [your_admin_password] -t "test/#" -v
```

**Expected result**: Successfully subscribed, waiting for messages.

---

## Troubleshooting

### Bridge Service Can't Connect

**Symptom**: Bridge logs show "Connection refused" or "Authentication failed"

**Solution**:
1. Check that `.env` file has correct `MQTT_USERNAME` and `MQTT_PASSWORD`
2. Verify the password matches what was generated
3. Restart the bridge: `docker compose restart mqtt-bridge`

### CR6 Can't Connect

**Symptom**: MQTT State shows connection errors

**Solution**:
1. Double-check username is exactly `cr6_datalogger`
2. Verify password is entered correctly (case-sensitive)
3. Ensure MQTT is still enabled in CR6 settings
4. Check broker logs: `docker compose logs mosquitto`

### Forgot Passwords

**Solution**:
1. Restore backup configuration: `cp config/mosquitto.conf.backup config/mosquitto.conf`
2. Restart broker: `docker compose restart mosquitto`
3. Run `./setup_mqtt_auth.sh` again to generate new passwords
4. Run `./enable_mqtt_auth.sh` to re-enable authentication

### Need to Add More Users

**Solution**:

```bash
# Add a new user
docker compose exec mosquitto mosquitto_passwd /mosquitto/config/passwd new_username

# Restart broker
docker compose restart mosquitto
```

---

## Security Best Practices

### Password Management

- ✅ Use the generated random passwords (don't create your own weak passwords)
- ✅ Store passwords in a secure password manager
- ✅ Never commit passwords to Git repositories
- ✅ Use different passwords for each account
- ❌ Don't share passwords between users
- ❌ Don't write passwords on paper or in plain text files

### Access Control

- Use `cr6_datalogger` account only for CR6 devices
- Use `mqtt_bridge` account only for the bridge service
- Use `admin` account only for testing and monitoring
- Create separate accounts for different CR6 devices if needed

### Regular Maintenance

- Change passwords every 90 days
- Review access logs regularly
- Remove accounts for decommissioned devices
- Monitor for failed authentication attempts

---

## Advanced: Per-Device Credentials

For enhanced security, you can create a separate account for each CR6 datalogger:

```bash
# Create account for CR6 #1
docker compose exec mosquitto mosquitto_passwd /mosquitto/config/passwd cr6_station_001

# Create account for CR6 #2
docker compose exec mosquitto mosquitto_passwd /mosquitto/config/passwd cr6_station_002

# Restart broker
docker compose restart mosquitto
```

Then configure each CR6 with its unique credentials.

---

## Backup and Recovery

### Backup Password File

```bash
# Create backup
cp config/passwd config/passwd.backup

# Restore from backup
cp config/passwd.backup config/passwd
docker compose restart mosquitto
```

### Export User List

```bash
# View all usernames (not passwords)
docker compose exec mosquitto cat /mosquitto/config/passwd | cut -d: -f1
```

---

## Summary

After completing this guide:

✅ Your MQTT broker requires authentication
✅ You have three accounts with strong passwords
✅ Your CR6 dataloggers can connect securely
✅ Your bridge service can access the broker
✅ Unauthorized access is blocked

**Next Steps**: Configure TLS/SSL encryption for additional security (see main README.md).

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review broker logs: `docker compose logs mosquitto`
3. Review bridge logs: `docker compose logs mqtt-bridge`
4. Verify credentials are correct in all locations
