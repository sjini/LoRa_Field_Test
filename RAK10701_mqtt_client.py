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
# Author:        Sergi Jini
# Date:          19.05.23
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
            enqueue_downlink(device_eui,payload)
            integrity_check = True                                          # Integrity check flag. Reserved for future revision
        except:
            print('Uplink data corrupted')
            integrity_check = False


# Schedule downlink for the device
def enqueue_downlink(dev_euid, payload):
    try:    
        Hexstr = bytes(payload).hex()                                       # Convert array to HEX
        HexToBase64 = base64.b64encode(bytes.fromhex(Hexstr)).decode()      # Convert HEX to base64
        packettosend = {"devEui": dev_euid,"confirmed":False,"fPort":"2","data":HexToBase64}
        json_packettosend = json.dumps(packettosend)
        client.publish("application/" + application_id + "/device/" + dev_euid + "/command/down", json_packettosend, 0, False)    
        print(json_packettosend)
        print(payload)
    except:
        print('Error while converting payload to HEX/base64')


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

application_id='1699a6c3-ca09-4365-8193-fd6ec1d069c8'                       # Application ID from ChirpStack
broker_address="localhost"                                                  # IP of the MQTT server. In this case script runs on same machine where MQTT service resides
broker_port=1883                                                            # Broker port. Change it in case your broker uses non standard port. Chirpstack default is 1883
client = mqtt.Client("P1")                                                  # Create new instance
client.on_message=on_message                                                # Attach function to callback
print("Connecting to broker")
client.connect(broker_address, broker_port)                                 # Connect to broker

# Need to add on connect procedure here, to loop until connection is established. client.on_connect = on_connect    

client.loop_start()                                                         # Start the loop
print("Subscribing to topic")
client.subscribe("application/"+application_id+"/#")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print ("exiting")
    client.disconnect()
    client.loop_stop()

