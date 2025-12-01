#!/usr/bin/env python3
"""
CR6 Data Simulator
Simulates Campbell Scientific CR6 datalogger publishing data to MQTT broker.
"""

import json
import time
import random
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# Configuration
MQTT_BROKER = "138.68.158.9"
MQTT_PORT = 1883
BASE_TOPIC = "cs/v1"
CLIENT_ID = "CR6_12345"  # Simulated CR6 serial number
TABLE_NAME = "Five_Min"

def generate_csijson_message():
    """
    Generate a sample CSIJSON message similar to CR6 output.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    record_number = int(time.time() % 10000)
    
    # Simulate sensor readings
    temp_c = round(random.uniform(20.0, 30.0), 2)
    humidity = round(random.uniform(40.0, 80.0), 2)
    batt_v = round(random.uniform(12.5, 13.2), 2)
    wind_speed = round(random.uniform(0.0, 15.0), 2)
    wind_dir = round(random.uniform(0.0, 360.0), 1)
    
    message = {
        "head": {
            "transaction": 0,
            "signature": 12345,
            "environment": {
                "station_name": CLIENT_ID,
                "table_name": TABLE_NAME,
                "model": "CR6",
                "serial_no": "12345",
                "os_version": "CR6.Std.11.00",
                "prog_name": "CPU:TestProgram.CR6"
            },
            "fields": [
                {"name": "TIMESTAMP", "type": "xsd:dateTime", "units": ""},
                {"name": "RECORD", "type": "xsd:long", "units": ""},
                {"name": "Temp_C_Avg", "type": "xsd:float", "units": "Deg C"},
                {"name": "Humidity_Avg", "type": "xsd:float", "units": "%"},
                {"name": "BattV_Min", "type": "xsd:float", "units": "Volts"},
                {"name": "WindSpeed_Avg", "type": "xsd:float", "units": "m/s"},
                {"name": "WindDir_Avg", "type": "xsd:float", "units": "degrees"}
            ]
        },
        "data": [
            [timestamp, record_number, temp_c, humidity, batt_v, wind_speed, wind_dir]
        ]
    }
    
    return message


def generate_status_message():
    """
    Generate a sample status message.
    """
    status = {
        "battery_voltage": round(random.uniform(12.5, 13.2), 2),
        "panel_temp": round(random.uniform(20.0, 35.0), 2),
        "program_name": "TestProgram.CR6",
        "os_version": "CR6.Std.11.00",
        "compile_time": "2025-12-01 10:00:00",
        "memory_free": random.randint(50000, 100000),
        "uptime_seconds": random.randint(10000, 1000000)
    }
    
    return status


def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker."""
    if rc == 0:
        print(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"✗ Failed to connect, return code: {rc}")


def on_publish(client, userdata, mid):
    """Callback when message is published."""
    print(f"  Message published (mid: {mid})")


def main():
    """
    Main function to run the CR6 simulator.
    """
    print("=" * 60)
    print("CR6 Data Simulator")
    print("=" * 60)
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Base Topic: {BASE_TOPIC}")
    print("=" * 60)
    print()
    
    # Create MQTT client
    client = mqtt.Client(client_id=f"{CLIENT_ID}_simulator")
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        # Connect to broker
        print("Connecting to MQTT broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        
        time.sleep(2)  # Wait for connection
        
        # Publish data messages
        print("\nPublishing simulated CR6 data...")
        for i in range(5):
            # Generate and publish data table message
            data_topic = f"{BASE_TOPIC}/{CLIENT_ID}/datatables/{TABLE_NAME}"
            data_message = generate_csijson_message()
            
            result = client.publish(
                data_topic,
                json.dumps(data_message),
                qos=0
            )
            
            print(f"\n[{i+1}/5] Published to: {data_topic}")
            print(f"  Temperature: {data_message['data'][0][2]}°C")
            print(f"  Humidity: {data_message['data'][0][3]}%")
            print(f"  Battery: {data_message['data'][0][4]}V")
            
            time.sleep(2)
        
        # Publish status message
        print("\nPublishing status information...")
        status_topic = f"{BASE_TOPIC}/{CLIENT_ID}/statusInfo"
        status_message = generate_status_message()
        
        client.publish(
            status_topic,
            json.dumps(status_message),
            qos=0
        )
        
        print(f"Published to: {status_topic}")
        print(f"  Battery Voltage: {status_message['battery_voltage']}V")
        print(f"  Panel Temperature: {status_message['panel_temp']}°C")
        
        time.sleep(2)
        
        print("\n" + "=" * 60)
        print("✓ Simulation complete!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("\nDisconnected from MQTT broker")


if __name__ == "__main__":
    main()
