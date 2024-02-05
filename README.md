# Python based STM32F4_Bootloader
 A Python based serial bootloader for STM32F4-series microcontroller, no PC-host GUI.

## 1. Stm32F4x_bootloader.py function
    
No GUI created in PC with the script. Debugged with Visual Studio Code Version 1.65.0 and stm32F411 Nucleo board. 

The python script calls ST bootloader commands to perform the following tasks: 
Erasing the Flash Section 7;
Then, writing the example bin file user_app.bin to the flash whose address starts from 0x0807c010. (This address can be changed by changing conf’s address in the code.) 
Verifying the codes. 

## 2. Use Hex Editor Neo to read and edit the bin file 

Before writing the bin file to STM32F4 flash, we can open the bin file with Hex Editor Neo to read and change the bin value. Here is the example:

![image](https://github.com/shilianzhao/Python-based-STM32F4-Bootloader/assets/31520270/ca64565d-9535-4406-88ff-8f93f8e90861)

## 3.	Use STM32CubeProgrammer to read the STM32F411 Nucleo board flash to confirm the writing

 ![image](https://github.com/shilianzhao/Python-based-STM32F4-Bootloader/assets/31520270/af781af1-5492-4d38-9b75-9284180067bc)

 ![image](https://github.com/shilianzhao/Python-based-STM32F4-Bootloader/assets/31520270/0b5cdf40-08da-4436-b925-ced74f93e4a7)

## 4.	Reference:

* STM file: AN2606_STM32 microcontroller system memory boot mode.pdf
* STM file: AN3155_USART protocol used in STM32 bootloader.pdf
* https://github.com/florisla/stm32loader florisla     very important
* https://github.com/jsnyder/stm32loader/blob/master/stm32loader.py, jsnyder
* https://github.com/pavelrevak/stm32bl/blob/ae908e34cdb727808817d2d04a6dbc752a5b22f8/README.md
* https://blog.csdn.net/qq_34254642/article/details/102887517 chinese  
* https://www.bilibili.com/video/BV1Ub4y167XQ/?spm_id_from=333.788.recommend_more_video.-1, STM32+IAP上位机程序讲解
* https://www.youtube.com/watch?v=GR8Vy5QvDHU STM32 Tips: Talking to the on-board Bootloader

## 5. Extra tool

AccessPort is useful for sending STM Bootloader command one-by-one to F411 Nucleo board.
![image](https://github.com/shilianzhao/Python-based-STM32F4-Bootloader/assets/31520270/498dde6f-2cee-48ec-a310-74352ca56285)



