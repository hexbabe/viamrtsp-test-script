# Guided Testing Script for `viamrtsp` for minor veresion release

## Overview

This script is designed to streamline the release process for the `viamrtsp` module by guiding the user through a series of steps to ensure that the module is working as expected. It provides a structured approach to testing the module's functionality, helping to identify and resolve any issues or bugs.

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

- Make a .env file in this directory with the following variables:
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
