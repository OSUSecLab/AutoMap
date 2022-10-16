# AutoMap

/usr/bin/JLinkGDBServer -If SWD -Speed 4000 -Device Cortex-M4
openocd -f interface/stlink-v2-1.cfg -f target/stm32f1x_stlink.cf
openocd -f interface/stlink-v2-1.cfg -f target/stm32f4x_stlink.cfg
