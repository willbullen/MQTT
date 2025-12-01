# Mosquitto MQTT Broker Docker Setup

**Author**: Manus AI
**Date**: December 1, 2025

## 1. Introduction

This repository provides a simple, containerized setup for deploying an **Eclipse Mosquitto MQTT broker** using Docker. It is designed for quick deployment on any server with Docker, such as a DigitalOcean droplet.

This setup is ideal for IoT projects, real-time messaging, and any application requiring a lightweight and reliable message broker.

### Key Features

- **Containerized with Docker**: Easy to deploy, manage, and scale.
- **Persistent Storage**: MQTT data and logs are stored on the host machine to survive container restarts.
- **WebSocket Support**: Includes configuration for MQTT over WebSockets on port `9001`.
- **Simple Configuration**: A clean and straightforward setup focused purely on the broker.

## 2. Project Structure

The repository contains the minimal files needed to run the Mosquitto broker.

```
MQTT/
├── docker-compose.yml       # Docker Compose file to run the broker
├── config/
│   └── mosquitto.conf       # Mosquitto broker configuration file
├── data/                    # (Created on run) For persistent MQTT data
└── log/                     # (Created on run) For Mosquitto log files
```

## 3. Deployment

Follow these steps to deploy the MQTT broker on your server.

### Prerequisites

- A server with Docker and Docker Compose installed.
- Git installed on the server.
- Firewall access to allow traffic on ports `1883` (MQTT) and `9001` (WebSockets).

### Step-by-Step Deployment

1.  **Clone the Repository**

    Connect to your server via SSH and clone this GitHub repository.

    ```bash
    git clone https://github.com/willbullen/MQTT.git
    cd MQTT
    ```

2.  **Create Directories and Set Permissions**

    Mosquitto runs as a non-root user inside the container (UID `1883`). You need to create the data and log directories on the host and give this user ownership.

    ```bash
    mkdir -p data log
    sudo chown -R 1883:1883 data log config
    ```

3.  **Start the MQTT Broker**

    Use Docker Compose to start the broker in detached mode.

    ```bash
    docker compose up -d
    ```

4.  **Verify the Deployment**

    Check that the container is running and healthy.

    ```bash
    docker compose ps
    ```

    You should see the `mosquitto` container with a status of `Up`.

## 4. Configuration

The broker's behavior is controlled by `config/mosquitto.conf`.

### Default Configuration

- **Anonymous Access**: `allow_anonymous true` (Enabled by default for easy setup).
- **Persistence**: Enabled, with data stored in the `./data` directory.
- **Logging**: Logs are written to `./log/mosquitto.log` and also sent to the Docker logs.

### Securing Your Broker (Recommended)

For any production or public-facing deployment, you should disable anonymous access and require authentication.

1.  **Create a Password File**

    Use this command to create a new user. You will be prompted to enter a password.

    ```bash
    docker compose exec mosquitto mosquitto_passwd -c /mosquitto/config/passwd your_username
    ```

2.  **Update Mosquitto Configuration**

    Edit `config/mosquitto.conf` and make the following changes:

    ```ini
    # allow_anonymous true  <-- Comment out or remove this line
    allow_anonymous false
    password_file /mosquitto/config/passwd
    ```

3.  **Restart the Broker**

    Apply the changes by restarting the container.

    ```bash
    docker compose restart
    ```

## 5. Testing the Broker

You can test your broker using any MQTT client or the `mosquitto-clients` command-line tools.

### Prerequisites

If you don't have the clients installed on your local machine, you can install them:

```bash
# On Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y mosquitto-clients

# On macOS (using Homebrew)
brew install mosquitto
```

### Test Commands

Replace `<your-server-ip>` with your droplet's IP address (e.g., `138.68.158.9`).

1.  **Subscribe to a Topic** (in one terminal window)

    ```bash
    mosquitto_sub -h <your-server-ip> -t "test/topic" -v
    ```

2.  **Publish a Message** (in a second terminal window)

    ```bash
    mosquitto_pub -h <your-server-ip> -t "test/topic" -m "Hello, MQTT!"
    ```

You should see "Hello, MQTT!" appear in the subscriber's terminal window.

## 6. Managing the Broker

Here are the basic commands for managing the Mosquitto service.

- **View Logs**: `docker compose logs -f mosquitto`
- **Stop the Broker**: `docker compose down`
- **Restart the Broker**: `docker compose restart`
- **Check Status**: `docker compose ps`

## 7. References

- [1] [Eclipse Mosquitto Official Documentation](https://mosquitto.org/documentation/)
- [2] [Docker Compose Documentation](https://docs.docker.com/compose/)
