# STM32F4_Bootloader_emailToLeo
 A Python based serial bootloader for STM32F4-series microcontroller, no PC-host GUI.

1. Stm32F4x_bootloader.py function
    
No GUI created in PC with the script. Debugged with Visual Studio Code Version 1.65.0 and stm32F411 Nucleo board. 

The python script calls ST bootloader commands to perform the following tasks: 
Erasing the Flash Section 7;
Then, writing the example bin file user_app.bin to the flash whose address starts from 0x0807c010. (This address can be changed by changing conf’s address in the code.) 
Verifying the codes. 


