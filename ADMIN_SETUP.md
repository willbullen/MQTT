# MQTT Admin User Setup

## Quick Setup

To add an admin user and enable authentication on your MQTT broker:

```bash
cd /root/MQTT
./setup_admin.sh
```

This will:
1. Create an admin user with username `admin` and password `B@ff1ed!2025`
2. Update the Mosquitto configuration to require authentication
3. Restart the broker to apply changes

## Credentials

After running the setup script:

- **MQTT Broker**: 138.68.158.9:1883
- **Username**: `admin`
- **Password**: `B@ff1ed!2025`

## Testing

### Publish a Message

```bash
mosquitto_pub -h 138.68.158.9 -u admin -P 'B@ff1ed!2025' -t "test/topic" -m "Hello MQTT"
```

### Subscribe to a Topic

```bash
mosquitto_sub -h 138.68.158.9 -u admin -P 'B@ff1ed!2025' -t "test/#" -v
```

## Adding More Users

To add additional users:

```bash
# Add a new user (you'll be prompted for password)
docker compose exec mosquitto mosquitto_passwd /mosquitto/config/passwd username

# Or add with password in command
docker compose exec mosquitto mosquitto_passwd -b /mosquitto/config/passwd username password

# Restart broker
docker compose restart mosquitto
```

## Removing Authentication

To disable authentication and allow anonymous access again:

```bash
# Restore original configuration
cp config/mosquitto.conf.backup config/mosquitto.conf

# Restart broker
docker compose restart mosquitto
```

## Security Notes

- Authentication is now **required** for all MQTT connections
- Anonymous access is **disabled**
- The password file is stored at `config/passwd` (encrypted)
- Keep your credentials secure and don't commit them to public repositories
