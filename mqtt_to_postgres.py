#!/usr/bin/env python3
"""
MQTT to PostgreSQL Bridge Service
Subscribes to MQTT topics from Campbell Scientific CR6 dataloggers
and stores the data in a PostgreSQL database.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

import paho.mqtt.client as mqtt
import psycopg2
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/MQTT/log/mqtt_bridge.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
MQTT_BROKER = os.getenv('MQTT_BROKER', '138.68.158.9')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'cs/v1/#')  # Subscribe to all CR6 topics
MQTT_CLIENT_ID = os.getenv('MQTT_CLIENT_ID', 'mqtt_postgres_bridge')

# PostgreSQL configuration
DB_HOST = os.getenv('DB_HOST', 'obs.valentiamet.com')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin123')

# Global database connection
db_conn = None


def connect_database() -> Optional[psycopg2.extensions.connection]:
    """
    Establish connection to PostgreSQL database.
    
    Returns:
        Database connection object or None if connection fails
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10
        )
        logger.info(f"Connected to PostgreSQL database at {DB_HOST}:{DB_PORT}")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        return None


def create_tables(conn: psycopg2.extensions.connection) -> None:
    """
    Create necessary database tables if they don't exist.
    
    Args:
        conn: Database connection object
    """
    try:
        cursor = conn.cursor()
        
        # Create table for raw MQTT messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mqtt_messages (
                id SERIAL PRIMARY KEY,
                topic VARCHAR(255) NOT NULL,
                payload JSONB,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_topic (topic),
                INDEX idx_received_at (received_at)
            );
        """)
        
        # Create table for CR6 sensor data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cr6_sensor_data (
                id SERIAL PRIMARY KEY,
                station_name VARCHAR(100),
                table_name VARCHAR(100),
                timestamp TIMESTAMP,
                record_number INTEGER,
                data JSONB,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_station (station_name),
                INDEX idx_timestamp (timestamp)
            );
        """)
        
        # Create table for CR6 status information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cr6_status (
                id SERIAL PRIMARY KEY,
                station_name VARCHAR(100),
                status_data JSONB,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_station_status (station_name)
            );
        """)
        
        conn.commit()
        logger.info("Database tables created successfully")
        
    except psycopg2.Error as e:
        logger.error(f"Failed to create tables: {e}")
        conn.rollback()
    finally:
        cursor.close()


def parse_csijson(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse Campbell Scientific JSON format.
    
    Args:
        payload: JSON payload from MQTT message
        
    Returns:
        Parsed data dictionary or None if parsing fails
    """
    try:
        if 'head' not in payload or 'data' not in payload:
            return None
            
        head = payload['head']
        data_rows = payload['data']
        
        environment = head.get('environment', {})
        fields = head.get('fields', [])
        
        station_name = environment.get('station_name', 'unknown')
        table_name = environment.get('table_name', 'unknown')
        
        parsed_data = {
            'station_name': station_name,
            'table_name': table_name,
            'environment': environment,
            'fields': fields,
            'records': []
        }
        
        # Parse each data row
        for row in data_rows:
            if len(row) >= 2:
                record = {
                    'timestamp': row[0],
                    'record_number': row[1],
                    'values': {}
                }
                
                # Map field names to values
                for i, field in enumerate(fields[2:], start=2):
                    if i < len(row):
                        record['values'][field['name']] = row[i]
                
                parsed_data['records'].append(record)
        
        return parsed_data
        
    except Exception as e:
        logger.error(f"Failed to parse CSIJSON: {e}")
        return None


def store_message(conn: psycopg2.extensions.connection, topic: str, payload: str) -> None:
    """
    Store raw MQTT message in database.
    
    Args:
        conn: Database connection object
        topic: MQTT topic
        payload: Message payload as string
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO mqtt_messages (topic, payload) VALUES (%s, %s)",
            (topic, payload)
        )
        conn.commit()
        logger.debug(f"Stored raw message from topic: {topic}")
    except psycopg2.Error as e:
        logger.error(f"Failed to store message: {e}")
        conn.rollback()
    finally:
        cursor.close()


def store_sensor_data(conn: psycopg2.extensions.connection, parsed_data: Dict[str, Any]) -> None:
    """
    Store parsed sensor data in database.
    
    Args:
        conn: Database connection object
        parsed_data: Parsed CSIJSON data
    """
    try:
        cursor = conn.cursor()
        
        station_name = parsed_data['station_name']
        table_name = parsed_data['table_name']
        
        # Insert each record
        for record in parsed_data['records']:
            cursor.execute(
                """
                INSERT INTO cr6_sensor_data 
                (station_name, table_name, timestamp, record_number, data)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    station_name,
                    table_name,
                    record['timestamp'],
                    record['record_number'],
                    json.dumps(record['values'])
                )
            )
        
        conn.commit()
        logger.info(f"Stored {len(parsed_data['records'])} records from {station_name}/{table_name}")
        
    except psycopg2.Error as e:
        logger.error(f"Failed to store sensor data: {e}")
        conn.rollback()
    finally:
        cursor.close()


def store_status_data(conn: psycopg2.extensions.connection, station_name: str, status_data: Dict[str, Any]) -> None:
    """
    Store CR6 status information in database.
    
    Args:
        conn: Database connection object
        station_name: Name of the station
        status_data: Status information
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO cr6_status (station_name, status_data)
            VALUES (%s, %s)
            """,
            (station_name, json.dumps(status_data))
        )
        conn.commit()
        logger.info(f"Stored status data from {station_name}")
    except psycopg2.Error as e:
        logger.error(f"Failed to store status data: {e}")
        conn.rollback()
    finally:
        cursor.close()


def on_connect(client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int) -> None:
    """
    Callback when MQTT client connects to broker.
    
    Args:
        client: MQTT client instance
        userdata: User data
        flags: Connection flags
        rc: Connection result code
    """
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code: {rc}")


def on_disconnect(client: mqtt.Client, userdata: Any, rc: int) -> None:
    """
    Callback when MQTT client disconnects from broker.
    
    Args:
        client: MQTT client instance
        userdata: User data
        rc: Disconnection result code
    """
    if rc != 0:
        logger.warning(f"Unexpected disconnection from MQTT broker, return code: {rc}")
    else:
        logger.info("Disconnected from MQTT broker")


def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    """
    Callback when MQTT message is received.
    
    Args:
        client: MQTT client instance
        userdata: User data
        msg: MQTT message
    """
    global db_conn
    
    topic = msg.topic
    payload_str = msg.payload.decode('utf-8')
    
    logger.info(f"Received message on topic: {topic}")
    
    # Reconnect to database if connection is lost
    if db_conn is None or db_conn.closed:
        logger.warning("Database connection lost, reconnecting...")
        db_conn = connect_database()
        if db_conn is None:
            logger.error("Failed to reconnect to database, message will be lost")
            return
    
    try:
        # Store raw message
        store_message(db_conn, topic, payload_str)
        
        # Try to parse as JSON
        payload_json = json.loads(payload_str)
        
        # Check if it's CSIJSON format (from CR6 data table)
        if 'head' in payload_json and 'data' in payload_json:
            parsed_data = parse_csijson(payload_json)
            if parsed_data:
                store_sensor_data(db_conn, parsed_data)
        
        # Check if it's status information
        elif 'statusInfo' in topic:
            station_name = topic.split('/')[2] if len(topic.split('/')) > 2 else 'unknown'
            store_status_data(db_conn, station_name, payload_json)
        
    except json.JSONDecodeError:
        logger.warning(f"Received non-JSON message on topic: {topic}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def main():
    """
    Main function to run the MQTT to PostgreSQL bridge.
    """
    global db_conn
    
    logger.info("Starting MQTT to PostgreSQL Bridge Service")
    
    # Connect to database
    db_conn = connect_database()
    if db_conn is None:
        logger.error("Cannot start without database connection")
        sys.exit(1)
    
    # Create tables
    create_tables(db_conn)
    
    # Create MQTT client
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # Connect to MQTT broker
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        logger.info("MQTT client connected, starting loop...")
        
        # Start MQTT loop
        client.loop_forever()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Cleanup
        client.disconnect()
        if db_conn:
            db_conn.close()
        logger.info("MQTT to PostgreSQL Bridge Service stopped")


if __name__ == "__main__":
    main()
