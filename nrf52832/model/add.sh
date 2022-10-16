#!/bin/bash

nrfjprog --program inf.hex --sectorerase
arm-none-eabi-gdb-py < add_input 
