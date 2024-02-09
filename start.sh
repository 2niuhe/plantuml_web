#!/bin/bash

# start 1
java -jar plantuml.jar -picoweb:8000 &
# start 2
python main.py

# just keep this script running
while [[ true ]]; do
    sleep 30
done