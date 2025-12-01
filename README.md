# Campbell Scientific CR6 to PostgreSQL Data Pipeline via MQTT

**Author**: Manus AI
**Date**: December 1, 2025

## 1. Introduction

This repository provides a complete, containerized solution for routing sensor data from Campbell Scientific CR6 dataloggers to a PostgreSQL database. The system uses a Mosquitto MQTT broker to receive data, and a custom Python bridge service to parse and store the data in the database. This setup is designed for robust, scalable, and real-time environmental data collection and analysis.

### Key Features

- **Containerized Deployment**: The entire stack (MQTT broker and bridge service) is managed with Docker and Docker Compose for easy setup and portability.
- **Real-Time Data Ingestion**: Leverages the MQTT protocol for efficient, low-latency message passing from dataloggers.
- **Structured Data Storage**: Parses Campbell Scientific's native CSIJSON format and stores sensor readings in a structured PostgreSQL database.
- **Scalable Architecture**: Designed to handle multiple CR6 dataloggers simultaneously.
- **Comprehensive Documentation**: Includes full setup, configuration, testing, and troubleshooting instructions.

## 2. System Architecture

The data pipeline consists of four main components that work together to move data from the field to the database.

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Data Source** | Campbell Scientific CR6 | Collects sensor data and publishes it to the MQTT broker. |
| **Message Broker** | Eclipse Mosquitto | Receives messages from all dataloggers and routes them to subscribers. |
| **Data Bridge** | Python (Paho-MQTT, Psycopg2) | Subscribes to MQTT topics, parses CSIJSON data, and inserts it into the PostgreSQL database. |
| **Database** | PostgreSQL | Provides long-term storage for the sensor data, enabling analysis and visualization. |

## 3. Project Structure

The repository is organized with all necessary configuration and code in a consolidated structure.

```
MQTT/
├── docker-compose.yml        # Main Docker Compose file for all services
├── Dockerfile.bridge         # Dockerfile for the Python bridge service
├── config/
│   └── mosquitto.conf        # Mosquitto broker configuration
├── mqtt_to_postgres.py       # Python script for the bridge service
├── requirements.txt          # Python dependencies for the bridge
├── .env.example              # Example environment file for configuration
├── deploy.sh                 # Deployment script for the droplet
├── test_cr6_simulator.py     # Python script to simulate a CR6 for testing
└── README.md                 # This documentation file
```

## 4. Deployment

This system is designed to be deployed on a server, such as the 'Enviroscan' DigitalOcean droplet, using Docker.

### Prerequisites

- A server with Docker and Docker Compose installed.
- Git installed on the server.
- Firewall access to allow traffic on ports `1883` (MQTT) and `9001` (MQTT over WebSockets).

### Step-by-Step Deployment

1.  **Clone the Repository**

    Connect to your server via SSH and clone this GitHub repository.

    ```bash
    git clone https://github.com/willbullen/MQTT.git
    cd MQTT
    ```

2.  **Configure Environment Variables**

    Create an environment file from the example. This file will hold your database credentials and other sensitive settings.

    ```bash
    cp .env.example .env
    ```

    Now, **edit the `.env` file** with your specific database connection details. **Crucially, the database host `obs.valentiamet.com` is currently unreachable.** You must replace it with a valid IP address or a working hostname.

    ```ini
    # .env
    # MQTT Broker Configuration
    MQTT_BROKER=127.0.0.1
    MQTT_PORT=1883
    MQTT_TOPIC=cs/v1/#

    # PostgreSQL Database Configuration
    DB_HOST=YOUR_DATABASE_IP_OR_HOSTNAME  # <-- IMPORTANT: UPDATE THIS
    DB_PORT=5432
    DB_NAME=postgres
    DB_USER=admin
    DB_PASSWORD=admin123
    ```

3.  **Run the Deployment Script**

    The provided `deploy.sh` script will handle directory creation, permissions, and starting the services.

    ```bash
    chmod +x deploy.sh
    ./deploy.sh
    ```

    This command will build the bridge service container and start both the Mosquitto broker and the bridge service in detached mode.

4.  **Verify the Deployment**

    Check that both containers are running and healthy.

    ```bash
    docker compose ps
    ```

    You should see both `mosquitto` and `mqtt-bridge` with a status of `Up`.

## 5. Campbell Scientific CR6 Integration

To connect your CR6 dataloggers to the system, you must configure their MQTT settings using Campbell Scientific's **Device Configuration Utility**.

### CR6 Configuration Settings

| Setting | Value | Notes |
| :--- | :--- | :--- |
| **MQTT Enable** | `Enable MQTT` | Use TLS options for production. |
| **MQTT Broker URL** | `138.68.158.9` | The IP address of your 'Enviroscan' droplet. |
| **MQTT Port Number** | `1883` | The standard MQTT port. |
| **MQTT Client ID** | `CR6_[SerialNumber]` | Must be unique for each datalogger. |
| **MQTT Base Topic** | `cs/v1/` | The default base topic. |

### CRBasic Program Example

Use the `MQTTPublishTable()` instruction within your data table definition in your CRBasic program to send data to the broker.

```basic
' CRBasic Program to Publish Sensor Data via MQTT

DataTable(SensorData, True, -1)
  DataInterval(0, 15, Min, 10)
  Average(1, AirTemp, FP2, False)
  Average(1, RH, FP2, False)

  ' Publish this table via MQTT every 15 minutes
  ' QoS=1 ensures message is delivered at least once
  MQTTPublishTable(1, 0, 15, Min, 1, NaN, NaN, NaN)
EndTable
```

Data will be published in CSIJSON format to a topic like `cs/v1/CR6_12345/datatables/SensorData`.

## 6. Testing and Validation

### Testing with the CR6 Simulator

Before connecting a real CR6, you can test the entire pipeline using the provided simulator script. This script will publish sample data to the broker, which the bridge service should then process and store in the database.

1.  **Run the Simulator**

    Execute the test script from within the sandbox or any machine with Python and `paho-mqtt` installed.

    ```bash
    python3 test_cr6_simulator.py
    ```

2.  **Monitor Bridge Logs**

    Watch the logs of the bridge service to see messages being received and processed.

    ```bash
    docker compose logs -f mqtt-bridge
    ```

    You should see log entries indicating messages are being received, parsed, and stored.

3.  **Verify Data in PostgreSQL**

    Connect to your PostgreSQL database and query the tables to confirm that the data has been inserted.

    ```sql
    -- Check for raw messages
    SELECT * FROM mqtt_messages ORDER BY received_at DESC LIMIT 5;

    -- Check for parsed sensor data
    SELECT station_name, timestamp, data->>'Temp_C_Avg' AS temperature
    FROM cr6_sensor_data
    ORDER BY timestamp DESC LIMIT 5;
    ```

## 7. Production Recommendations

For a production environment, it is critical to enhance the security and reliability of the system.

### Securing the MQTT Broker

By default, the broker allows anonymous connections. You should disable this and enforce authentication.

1.  **Create a Password File**

    ```bash
    docker compose exec mosquitto mosquitto_passwd -c /mosquitto/config/passwd your_cr6_username
    ```

2.  **Update Mosquitto Configuration**

    Edit `config/mosquitto.conf` and change the following lines:

    ```ini
    allow_anonymous false
    password_file /mosquitto/config/passwd
    ```

3.  **Restart the Broker**

    ```bash
    docker compose restart mosquitto
    ```

4.  **Update CR6 and Bridge Settings**: Remember to update the username/password in your CR6 datalogger settings and in the `.env` file for the bridge service.

### Enabling TLS Encryption

For end-to-end encryption, configure Mosquitto and your CR6 dataloggers to use TLS. This involves generating certificates and updating the respective configurations. Refer to the official Mosquitto and Campbell Scientific documentation for detailed instructions.

## 8. Troubleshooting

- **Database Connection Failure**: The most likely initial issue. The `mqtt-bridge` logs will show `Failed to connect to database`. Ensure the `DB_HOST` in your `.env` file is correct and the database server is accessible from your droplet.
- **Permission Denied**: If `deploy.sh` fails with permission errors, ensure you are running it as a user with Docker privileges (or use `sudo`).
- **Bridge Not Receiving Messages**: Check the `MQTT_BROKER` address in the `.env` file. It should be `127.0.0.1` if running on the same host. Also, verify the MQTT broker is running correctly with `docker compose logs mosquitto`.

## 9. References

- [1] [Eclipse Mosquitto Official Documentation](https://mosquitto.org/documentation/)
- [2] [Campbell Scientific CR6 Manual - MQTT Section](https://help.campbellsci.com/cr6/Content/shared/Communication/mqtt/mqtt.htm)
- [3] [PostgreSQL Official Documentation](https://www.postgresql.org/docs/)
- [4] [Docker Compose Documentation](https://docs.docker.com/compose/)
