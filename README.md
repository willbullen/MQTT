# Mosquitto MQTT Broker Docker Setup

This repository contains the Docker configuration for running an Eclipse Mosquitto MQTT broker on a DigitalOcean droplet.

## Overview

**Mosquitto** is an open-source message broker that implements the MQTT (Message Queuing Telemetry Transport) protocol. This setup uses Docker to deploy Mosquitto with persistent storage and WebSocket support.

## Features

- **MQTT Protocol** on port 1883
- **WebSocket Support** on port 9001
- **Persistent Data Storage**
- **Logging** to file and stdout
- **Auto-restart** on failure

## Project Structure

```
MQTT/
├── docker-compose.yml       # Docker Compose configuration
├── config/
│   └── mosquitto.conf       # Mosquitto broker configuration
├── data/                    # Persistent MQTT data (created on first run)
└── log/                     # Log files (created on first run)
```

## Prerequisites

- Docker installed on your server
- Docker Compose installed
- Firewall configured to allow ports 1883 and 9001

## Installation on DigitalOcean Droplet 'Enviroscan'

### 1. Clone this repository

```bash
git clone https://github.com/willbullen/MQTT.git
cd MQTT
```

### 2. Create required directories

```bash
mkdir -p data log
```

### 3. Set proper permissions

```bash
sudo chown -R 1883:1883 data log
```

### 4. Start the MQTT broker

```bash
docker compose up -d
```

### 5. Verify the broker is running

```bash
docker compose ps
docker compose logs -f mosquitto
```

## Configuration

The Mosquitto configuration is located in `config/mosquitto.conf`. Key settings include:

- **Anonymous Access**: Currently enabled (`allow_anonymous true`) - **Change this for production!**
- **Persistence**: Enabled with data stored in `/mosquitto/data/`
- **Logging**: Both file and stdout logging enabled

### Security Recommendations

For production use, you should:

1. **Disable anonymous access** and configure authentication:
   ```bash
   # Create password file
   docker compose exec mosquitto mosquitto_passwd -c /mosquitto/config/passwd username
   ```

2. **Update mosquitto.conf** to use authentication:
   ```conf
   allow_anonymous false
   password_file /mosquitto/config/passwd
   ```

3. **Enable TLS/SSL** for encrypted connections

4. **Configure firewall rules** to restrict access

## Usage

### Start the broker

```bash
docker compose up -d
```

### Stop the broker

```bash
docker compose down
```

### View logs

```bash
docker compose logs -f mosquitto
```

### Restart the broker

```bash
docker compose restart
```

## Testing the MQTT Broker

### Using mosquitto_pub and mosquitto_sub

Install MQTT clients on your local machine:

```bash
# Ubuntu/Debian
sudo apt-get install mosquitto-clients

# macOS
brew install mosquitto
```

**Subscribe to a topic:**

```bash
mosquitto_sub -h <your-droplet-ip> -t "test/topic" -v
```

**Publish a message:**

```bash
mosquitto_pub -h <your-droplet-ip> -t "test/topic" -m "Hello MQTT!"
```

## Firewall Configuration

If using UFW on your DigitalOcean droplet:

```bash
sudo ufw allow 1883/tcp
sudo ufw allow 9001/tcp
sudo ufw reload
```

## Monitoring

Monitor the broker status:

```bash
# Check container status
docker compose ps

# View real-time logs
docker compose logs -f

# Check resource usage
docker stats mosquitto
```

## Troubleshooting

### Container won't start

Check logs for errors:
```bash
docker compose logs mosquitto
```

### Permission issues

Ensure proper ownership:
```bash
sudo chown -R 1883:1883 data log config
```

### Connection refused

- Verify the container is running: `docker compose ps`
- Check firewall rules: `sudo ufw status`
- Verify port bindings: `docker port mosquitto`

## Backup

To backup your MQTT data:

```bash
tar -czf mqtt-backup-$(date +%Y%m%d).tar.gz data/ config/
```

## License

This project uses Eclipse Mosquitto, which is licensed under the Eclipse Public License 2.0 (EPL-2.0).

## Support

For issues related to Mosquitto, visit the [official documentation](https://mosquitto.org/documentation/).
