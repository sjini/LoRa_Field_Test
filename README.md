# MQTT listener/publisher for RAK10701 Lora Field test device

Code assembled in refference to following quick start guide - https://docs.rakwireless.com/Product-Categories/WisNode/RAK10701-P/Quickstart/#lorawan-network-servers-guide-for-rak10701-p-field-tester-pro

This is a Mqtt listener/publisher for LoRa Field tester (RAK10701). This script should be run as service on your ChirpStack server.
You will need to set parameter <application_id> to match yours. You can obtain it either from ChirpStack GUI or via ChirpStack API.
It is possible to run the script on different machine (other than ChirpStack server), but you will need to change the <broker_address> to match your ChirpStask IP and configure mqtt authentication (username, password, jwt..).
On downlink, device expects 6 values as an array. Here is a sample

               [1, 140, 147, 1, 23, 2]
                │   │    │   │   │  └───── Number of Gateways
                │   │    │   │   └──────── Maximum Distance from Gateway
                │   │    │   └──────────── Minimum Distance from Gateway
                │   │    └──────────────── Maximum RSSI value
                │   └───────────────────── Minimum RSSI value
                └───────────────────────── Downlink counter. incremental

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

It is recommended that RAK10701_mqtt_client.py script is installed as a service to ensure continuous uplink/downlink functionality.
Here is the setup, which I had at the moment of writing this code:

    Debian GNU/Linux 11 (bullseye)
    Python 3.9.2
    pip 20.3.4
    paho-mqtt 1.6.1 
    Chirpstack v4

## Usage

Prerequisite:
You should have the Chirpstack service running, Have at least 1 Gateway and RAK10701 node added as well (and Joined).
Upload the RAK10701_mqtt_client.py on your linux machine and make sure the script is executable (sudo chmod +x RAK10701_mqtt_client.py).
Create a Systemd service unit file: Systemd is the init system used by Debian. You need to create a service unit file to define your script as a service. Open a terminal and run the following command to create the service unit file:

    sudo nano /etc/systemd/system/myservice.service

Replace myservice with the desired service name.
Add the following content to the service unit file:


    [Unit]
    Description=My Service
    After=network.target

    [Service]
    ExecStart=/usr/bin/python3 /path/to/your/script.py

    [Install]
    WantedBy=default.target

Make sure to replace /path/to/your/script.py with the actual path to your Python script.
Save the file and exit the text editor.
Enable and start the service: Run the following commands to enable the service and start it:

    sudo systemctl enable myservice
    sudo systemctl start myservice

Replace myservice with the service name you specified in the service unit file.
Verify the service: Check the status of the service to ensure it is running properly:

    sudo systemctl status myservice

If everything is set up correctly, you should see the status as "active (running)".
From this moment, you should see data updated on RAK10701 screen

## To be done

1. Need to make first byte of downlink incremental (downlink counter). For now it is always set to 1



## License

Free license. Use/modidy however it fits your needs
