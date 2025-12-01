# Campbell Scientific CR6 MQTT Integration Guide

## Overview

The Campbell Scientific CR6 datalogger has native MQTT support built into its operating system. This allows the CR6 to publish sensor data directly to an MQTT broker without requiring additional software or middleware.

## CR6 MQTT Capabilities

The CR6 supports the following MQTT features:

- **Direct MQTT Publishing**: Uses the `MQTTPublishTable()` instruction to publish data tables
- **Automatic Publishing**: Can be configured to automatically publish data at specified intervals
- **TLS/SSL Support**: Supports encrypted connections with TLS and mutual authentication
- **Quality of Service (QoS)**: Supports QoS levels 0, 1, and 2
- **Persistent Sessions**: Maintains connection state and receives missed messages
- **JSON Format**: Publishes data in CSIJSON format (Campbell Scientific JSON)
- **WebSocket Support**: Can use WebSocket protocol for MQTT

## Required Configuration Information

Before configuring your CR6, gather the following information:

1. **MQTT Broker URL**: `138.68.158.9` (your Enviroscan droplet)
2. **Port Number**: `1883` (standard MQTT) or `9001` (WebSocket)
3. **Client ID**: Unique identifier for each CR6 (default: `CR6_SerialNumber`)
4. **Base Topic**: Default is `cs/v1/` (case sensitive)
5. **Username/Password**: Optional (currently not required as anonymous access is enabled)

## Configuration Steps

### Step 1: Connect to CR6 with Device Configuration Utility

1. Launch Campbell Scientific Device Configuration Utility
2. Connect to your CR6 datalogger
3. Navigate to the **Settings Editor** tab
4. Click on the **MQTT** sub-tab

### Step 2: Configure Basic MQTT Settings

Configure the following settings:

| Setting | Value | Description |
|---------|-------|-------------|
| **MQTT Enable** | Enable MQTT (option 3) | Enables MQTT without TLS for testing |
| **MQTT Broker URL** | `138.68.158.9` | Your Enviroscan droplet IP address |
| **MQTT Port Number** | `1883` | Standard MQTT port |
| **MQTT Connection** | Persistent (default) | Maintains session state |
| **MQTT Client ID** | `CR6_[SerialNumber]` | Must be unique for each datalogger |
| **MQTT Base Topic** | `cs/v1/` | Default base topic (case sensitive) |
| **MQTT Username** | (leave blank) | Not required with anonymous access |
| **MQTT Password** | (leave blank) | Not required with anonymous access |

### Step 3: Configure Optional Settings

| Setting | Default Value | Purpose |
|---------|---------------|---------|
| **Keep Alive** | 300 seconds | Time between ping packets |
| **Status Info Publish Interval** | 30 minutes | Frequency of status updates |
| **State Publish Interval** | 1 minute | Frequency of state updates |
| **MQTT Will Topic** | (optional) | Topic for last will message |
| **MQTT Will Message** | (optional) | Message sent on unexpected disconnect |

### Step 4: Apply Settings

1. Click **Apply** in Device Configuration Utility
2. The CR6 will connect to the MQTT broker
3. Monitor the **MQTT State** field to verify connection (should show state 50 = "MQTT session established")

## Programming the CR6

### Basic Example: Publishing Temperature Data

```basic
' CR6 CRBasic Program Example
' Publishes temperature data every 5 minutes via MQTT

Public Temp_C
Public BattV

' Define data table with MQTT publishing
DataTable(Five_Min, True, -1)
  DataInterval(0, 5, Min, 10)
  Average(1, Temp_C, FP2, False)
  Minimum(1, BattV, FP2, False, False)
  
  ' Publish every 5 minutes in CSIJSON format
  ' Parameters: QoS, Retain, Interval, Units, Format, Longitude, Latitude, Altitude
  MQTTPublishTable(0, 0, 5, Min, 1, NaN, NaN, NaN)
EndTable

' Main scan
BeginProg
  Scan(1, Sec, 0, 0)
    ' Measure temperature (example using thermocouple)
    TCDiff(Temp_C, 1, mV2_5C, 1, TypeT, PanelTemp, True, 0, 250, 1.0, 0)
    
    ' Measure battery voltage
    Battery(BattV)
    
    ' Call data table
    CallTable(Five_Min)
  NextScan
EndProg
```

### MQTTPublishTable() Instruction Parameters

```
MQTTPublishTable(QoS, Retain, Interval, Units, Format, Longitude, Latitude, Altitude)
```

**Parameters:**
- **QoS** (0-2): Quality of Service level
  - 0 = At most once (no confirmation)
  - 1 = At least once (confirmation required)
  - 2 = Exactly once (multi-step handshake)
- **Retain** (0 or 1): Whether broker should retain the message
- **Interval/Units**: How often to publish (e.g., 5, Min for every 5 minutes)
- **Format** (1): CSIJSON format
- **Longitude/Latitude/Altitude**: Geographic coordinates (use NaN if not applicable)

## MQTT Topic Structure

The CR6 publishes data to topics following this structure:

```
{BaseTopic}{ClientID}/datatables/{TableName}
```

**Example:**
```
cs/v1/CR6_12345/datatables/Five_Min
```

### Automatic Topics

The CR6 also publishes to these automatic topics:

- **Status Info**: `{BaseTopic}{ClientID}/statusInfo`
- **State**: `{BaseTopic}{ClientID}/State`
- **Online/Offline**: `{BaseTopic}{ClientID}/online` or `/offline`

## Data Format

The CR6 publishes data in **CSIJSON** (Campbell Scientific JSON) format:

```json
{
  "head": {
    "transaction": 0,
    "signature": 12345,
    "environment": {
      "station_name": "CR6_12345",
      "table_name": "Five_Min",
      "model": "CR6",
      "serial_no": "12345",
      "os_version": "CR6.Std.11.00",
      "prog_name": "CPU:MyProgram.CR6"
    },
    "fields": [
      {"name": "TIMESTAMP", "type": "xsd:dateTime", "units": ""},
      {"name": "RECORD", "type": "xsd:long", "units": ""},
      {"name": "Temp_C_Avg", "type": "xsd:float", "units": "Deg C"},
      {"name": "BattV_Min", "type": "xsd:float", "units": "Volts"}
    ]
  },
  "data": [
    ["2025-12-01T14:30:00", 1, 23.5, 12.8],
    ["2025-12-01T14:35:00", 2, 23.7, 12.8]
  ]
}
```

## Testing the Connection

### 1. Subscribe to CR6 Topics

From a computer with MQTT client tools installed:

```bash
# Subscribe to all topics from your CR6
mosquitto_sub -h 138.68.158.9 -t "cs/v1/CR6_#" -v

# Subscribe to specific data table
mosquitto_sub -h 138.68.158.9 -t "cs/v1/CR6_12345/datatables/Five_Min" -v
```

### 2. Monitor MQTT State

In Device Configuration Utility:
1. Go to **Settings Editor** > **MQTT** tab
2. Check the **MQTT State** field
3. State 50 = "MQTT session established" indicates successful connection

### 3. View Data Logger Status

```bash
# Subscribe to status information
mosquitto_sub -h 138.68.158.9 -t "cs/v1/CR6_+/statusInfo" -v
```

## Troubleshooting

### CR6 Won't Connect to Broker

**Check the following:**

1. **Network Connectivity**: Ensure CR6 has internet access
2. **Broker URL**: Verify `138.68.158.9` is correct
3. **Port Number**: Confirm port `1883` is open and accessible
4. **Firewall**: Ensure firewall allows incoming connections on port 1883
5. **MQTT State**: Check MQTT State field in Device Configuration Utility

### No Data Being Published

**Verify:**

1. **MQTTPublishTable() Instruction**: Ensure it's included in your DataTable declaration
2. **Data Table Execution**: Verify the data table is being called with `CallTable()`
3. **Publish Interval**: Check that enough time has passed for the first publish
4. **MQTT Enable**: Confirm MQTT is enabled in settings

### Connection Drops Frequently

**Solutions:**

1. **Increase Keep Alive**: Set to 600 seconds (10 minutes)
2. **Use Persistent Connection**: Ensure MQTTCleanSession is set to Persistent
3. **Check Network Stability**: Verify reliable internet connection
4. **Configure Last Will**: Set up Last Will Topic and Message for disconnect notifications

## Security Recommendations

For production deployment, implement the following security measures:

### 1. Enable Authentication

Configure username and password on the MQTT broker, then update CR6 settings:
- **MQTT Username**: Set to your broker username
- **MQTT Password**: Set to your broker password

### 2. Enable TLS Encryption

1. Configure TLS certificates on your MQTT broker
2. Change **MQTT Enable** to "Enable with TLS" (option 2)
3. Upload certificates to CR6 if using mutual authentication

### 3. Use Unique Client IDs

Ensure each CR6 has a unique Client ID to prevent connection conflicts.

### 4. Restrict Topic Access

Configure broker ACLs (Access Control Lists) to restrict which topics each client can publish/subscribe to.

## Network Requirements

The CR6 requires the following for MQTT operation:

- **Internet Connection**: Ethernet, WiFi, or cellular modem
- **Outbound Port Access**: Port 1883 (MQTT) or 9001 (WebSocket)
- **DNS Resolution**: If using domain names instead of IP addresses
- **Bandwidth**: Minimal (typically < 1 KB per message)

## Additional Resources

- **CR6 MQTT Documentation**: https://help.campbellsci.com/CR6/Content/shared/Communication/mqtt/mqtt.htm
- **CRBasic Editor Help**: https://help.campbellsci.com/crbasic/cr6/
- **Device Configuration Utility**: Available from Campbell Scientific website
- **MQTT Protocol Specification**: https://mqtt.org/
