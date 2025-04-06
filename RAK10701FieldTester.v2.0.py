# ====================================================================================================================================================================================
# Description:  This is a Mqtt listener/publisher for LoRa Field tester (RAK10701). This script should be run as service on your ChirpStack server.
#               You will need to set parameter <application_id> to match yours. You can optain it either from ChirpStack GUI or via ChirpStack API
#               It is possible to run the script on different machine (other than ChirpStack server), but you will need to change the <broker_address> to match your ChirpStask IP 
#               and configure mqtt authentication (username, password, jwt..)
#
#               On downlink, device expects 6 values as an array. Here is a sample
#               [1, 140, 147, 1, 23, 2]
#                │   │    │   │   │  └───── Number of Gateways
#                │   │    │   │   └──────── Maximum Distance from Gateway
#                │   │    │   └──────────── Minimum Distance from Gateway
#                │   │    └──────────────── Maximum RSSI value
#                │   └───────────────────── Minimum RSSI value
#                └───────────────────────── Proprietary. To be set as 1
#
# Author:	Sergi Jini
# Date:		19.05.23
# Revision:	04.04.25 (Python upgrade)
# ====================================================================================================================================================================================


import paho.mqtt.client as mqtt
import time
import base64
import json
import math
from math import radians, sin, cos, sqrt, atan2


# Process the data once payload arrives
def on_message(client, userdata, message):
    json_data = str(message.payload.decode("utf-8"))
    data = json.loads(json_data)                                            # Parse the JSON datavalues
    print("==========================================================\n")
    print(data)
    print("==========================================================\n")
    if next(iter(data)) == 'deduplicationId':                               # Access the first element using indexing to check if it is needed packet. In my case it should start with key 'deduplicationId'
        try:                                                                # Try extracting key values. In some cases json keys/values are not complete, resulting in script exception
            device_eui = data['deviceInfo']['devEui']
            device_lat = data['object']['latitude']
            device_long = data['object']['longitude']
            gw_number = len(data['rxInfo'])
            rx_info = data['rxInfo']                                        # Extract the "rxInfo" array
            rssi_values = [info['rssi'] for info in rx_info]                # Extract the RSSI values
            # Find the minimum and maximum RSSI values. "+200" is taken from article https://docs.rakwireless.com/Product-Categories/WisNode/RAK10701-P/Quickstart/#lorawan-network-servers-guide-for-rak10701-p-field-tester-pro
            min_rssi = min(rssi_values) + 200
            max_rssi = max(rssi_values) + 200

            # Find min and max distances
            location_array = [0] * gw_number                                # Create empty array
            for index,value in enumerate(rx_info):                          # Loop through each available location values
                lat_temp = round(value['location']['latitude'],5)
                long_temp = round(value['location']['longitude'],5)
                location_array[index] = calculate_distance(device_lat, device_long,lat_temp,long_temp)  # Caltulate distance and save each value in location array table
            min_distance = min(location_array)                              # Get the minimum value from location array
            max_distance = max(location_array)                              # Get the maximum value from location array

            # construct payload for downlink
            payload = [1,min_rssi,max_rssi,min_distance,max_distance,gw_number]
            print(payload)
            enqueue_downlink(device_eui,payload)
            integrity_check = True                                          # Integrity check flag. Reserved for future revision
        except:
            print('Uplink data corrupted')
            integrity_check = False


# Schedule downlink for the device
def enqueue_downlink(dev_euid, payload):
    try:

        # Ensure payload is a list of integers in range 0-255
        if not all(isinstance(i, int) and 0 <= i <= 255 for i in payload):
            raise ValueError("Payload must be a list of integers between 0-255")
        Hexstr = bytes(payload).hex()                                       # Convert array to HEX
        HexToBase64 = base64.b64encode(bytes.fromhex(Hexstr)).decode()      # Convert HEX to base64
        packettosend = {"devEui": dev_euid,"confirmed":False,"fPort":'2',"data":HexToBase64}
        json_packettosend = json.dumps(packettosend)
        client.publish("application/" + APPLICATION_ID + "/device/" + dev_euid + "/command/down", json_packettosend, 0, False)
        print("Downlink scheduled successfully!")
    except Exception and e:							# Capture the actual error
        print(f'Error while converting payload to HEX/base64: {e}')


# Calculate distance between 2 coordinates using Harvesine formula. Returns difference in meters / 250
def calculate_distance(lat1, lon1, lat2, lon2):
    lat1 = radians(lat1)                                                    # Convert latitude and longitude to radians
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    radius = 6371000                                                        # Radius of the Earth in meters
    dlat = lat2 - lat1                                                      # Calculate the differences of latitudes and longitudes
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2     # Haversine formula
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 1 + int((math.floor(radius * c))/250)                        # Device expects to receive 250m as value 1, 500m as value 2, etc..
    if distance > 255:                                                      # Avoid sending 63,750m as  value should be in 0-25>
       distance = 255

    return distance



# ===============================================  M A I N ======================================================

# MQTT Broker details
BROKER = ""					# Replace with your broker's address
PORT = 1883							# Default MQTT port
APPLICATION_ID = "" 	# Your specific application ID
TOPIC = f"application/{APPLICATION_ID}/device/+/event/#"	# Filter messages for this application


# Authentication
USERNAME = ""  						# Replace with your MQTT username
PASSWORD = ""					# Replace with your MQTT password

# Callback when connected to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker!")
        client.subscribe(TOPIC)					# Subscribe to wildcard topic
    else:
        print(f"Failed to connect, return code {rc}")


# Set up MQTT client
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)			# Set username and password
client.on_connect = on_connect
client.on_message = on_message

# Connect and listen
client.connect(BROKER, PORT, 60)
client.loop_forever()						# Keep listening
