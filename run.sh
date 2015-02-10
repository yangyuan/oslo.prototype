#!/bin/bash

screen -dmS prototype
screen -S prototype -p 0 -X stuff "keystone-all"
screen -S prototype -X screen -t 1
screen -S prototype -p 1 -X stuff "./bin/api --config-file etc/prototype/prototype.conf"
screen -S prototype -X screen -t 2
screen -S prototype -p 2 -X stuff "./bin/worker --config-file etc/prototype/prototype.conf"
