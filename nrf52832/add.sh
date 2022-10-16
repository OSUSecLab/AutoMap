#!/bin/bash

while true 
do
    rm -f model/add_regs.txt
    ./execute_firmware.py --firmware blinky.bin
    FILE=model/add_regs.txt
    if [ -f "$FILE" ]; then
        cat $FILE
        cd model
        ./add.sh
        cd ../
    else
        break
    fi
done
