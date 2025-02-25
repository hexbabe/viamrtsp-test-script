# Guided Testing Script for `viamrtsp` for minor version release

## Overview

This script is designed to streamline the release process for the `viamrtsp` module by guiding the user through a series of steps to ensure that the module is working as expected. It hits on the points Rand initially suggested in the process Google Calendar event:

- Test streaming on an h264, h265 camera on a Raspberry Pi and Jetson.
- Test reconfiguration by changing rtp_passthrough to false.
- Test ONVIF Discovery Service.
- Test video store uploading videos using Data Manager on a Raspberry Pi and Jetson. Ensure the video can be played and is as expected.
- Test video store reconfiguring from default to "ultrafast encoding".

## Prerequisites
- Download the robot config you want to test on in this working directory as `config.json`
```
sudo curl -H "<key-id>" -H "key:<key>" "https://app.viam.com/api/json1/config?id=<robot_id>&client=true" -o ./config.json
```
- Start .venv and install dependencies
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Make a .env file in this directory with the following variables. You can also ask Sean Yu for his file for av-orin-nano-3:
```
API_KEY=<your_api_key>
API_KEY_ID=<your_api_key_id>
PART_ID=<your_part_id>
MACHINE_ADDRESS=<your_machine_address>
ONVIF_USERNAME=<your_onvif_username>
ONVIF_PASSWORD=<your_onvif_password>
CAMERA_IP=<your_camera_ip>
```

## Run the script and follow the instructions
```
python3 ./script.py
```
