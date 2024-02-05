#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Modified: Steven Shilian Zhao
# Orignal Author: Ivan A-R <ivan@tuxotronic.org>
# Project page: http://tuxotronic.org/wiki/projects/stm32loader

# This file is part of stm32loader.
#
# stm32loader is distributed inside the chip in the hope that it will be useful for customer to call the it to downloader the bin file to flash. 

import sys
import serial
import time
import binascii


def mdebug(message):
    print(message)


class CmdException(Exception):
    pass

class CommandInterface:
    extended_erase = 0

    def __init__(self):
       pass 

    #def open(self, aport='/dev/tty.usbserial-ftCYPMYJ', abaudrate=115200) :
    def open(self, aport='COM10', abaudrate=57600) :
        self.sp = serial.Serial(
            port=aport,
            baudrate=abaudrate,     # baudrate
            bytesize=8,             # number of databits
            parity=serial.PARITY_EVEN,
            stopbits=1,
            xonxoff=0,              # don't enable software flow control
            rtscts=0,               # don't enable RTS/CTS flow control
            timeout=5               # set a timeout value, None for waiting forever
        )


    def _wait_for_ask(self, info = ""):
        # wait for ask
        try:
            ask = ord(self.sp.read())
        except:
            raise CmdException("Can't read port or timeout")
        else:
            if ask == 0x79:
                # ACK
                return 1
            else:
                if ask == 0x1F:
                    # NACK
                    raise CmdException("NACK "+info)
                else:
                    # Unknown responce
                    raise CmdException("Unknown response. "+info+": "+hex(ask))


    def reset(self):
        self.sp.setDTR(0)
        time.sleep(0.1)
        self.sp.setDTR(1)
        time.sleep(0.5)

    def initChip(self):
        # Set boot
        self.sp.setRTS(0)
        self.reset()
        send_data = b'\x7F'
        self.sp.write(send_data)      # successful in test/debug by steven 
        return self._wait_for_ask("Syncro")

    def releaseChip(self):
        self.sp.setRTS(1)
        self.reset()


    def cmdGeneric(self, cmd):     
        self.sp.write(int_to_hex(cmd))
        self.sp.write(int_to_hex(cmd ^ 0xFF))        # Control byte
        return self._wait_for_ask(hex(cmd))

 
    def cmdGet(self): 
#        if self.cmdGeneric(0x00):        # masked by steven
        self.sp.write(b'\x00')            # added by steven
        self.sp.write(b'\xFF')            # added by steven Control byte
        return_value = self._wait_for_ask('\x00')
        if return_value:
            mdebug("*** Get command")
            len = ord(self.sp.read())
            version = ord(self.sp.read())
            mdebug("    Bootloader version: "+hex(version))
            #dat = map(lambda c: hex(ord(c)), self.sp.read(len))
            dat = self.sp.read(len)
            
            if 0x44 in dat:
                self.extended_erase = 1

            self._wait_for_ask("0x00 end")
            return version
        else:
            raise CmdException("Get (0x00) failed")

    def cmdGetVersion(self):
        if self.cmdGeneric(0x01):
            mdebug("*** GetVersion command")
            version = ord(self.sp.read())
            self.sp.read(2)
            self._wait_for_ask("0x01 end")
            mdebug("    Bootloader version: "+hex(version))
            return version
        else:
            raise CmdException("GetVersion (0x01) failed")
    
    def _encode_addr(self, addr):
        byte3 = (addr >> 0) & 0xFF
        byte2 = (addr >> 8) & 0xFF
        byte1 = (addr >> 16) & 0xFF
        byte0 = (addr >> 24) & 0xFF
        crc = byte0 ^ byte1 ^ byte2 ^ byte3
        #return (chr(byte0) + chr(byte1) + chr(byte2) + chr(byte3) + chr(crc))  # this is original python 2 codes
        address_and_checksum = [byte0, byte1, byte2,byte3,crc]
        return address_and_checksum


    def cmdReadMemory(self, addr, lng):
        assert(lng <= 256)
        if self.cmdGeneric(0x11):
            mdebug("*** ReadMemory command")
            self.sp.write(self._encode_addr(addr))
            self._wait_for_ask("0x11 address failed")
            N = (lng - 1) & 0xFF
            crc = N ^ 0xFF
            self.sp.write(int_to_hex(N) + int_to_hex(crc))
            self._wait_for_ask("0x11 length failed")
            data_read = self.sp.read(lng)
            return data_read
        else:
            raise CmdException("ReadMemory (0x11) failed")


    def cmdGo(self, addr):
        if self.cmdGeneric(0x21):
            mdebug("*** Go command")
            self.sp.write(self._encode_addr(addr))
            self._wait_for_ask("0x21 go failed")
        else:
            raise CmdException("Go (0x21) failed")


    def cmdWriteMemory(self, addr, data):      #write all the data, can be < 256
        assert(len(data) <= 256)
        if self.cmdGeneric(0x31):  #masked by steven
            mdebug("*** Write memory command")
            self.sp.write(self._encode_addr(addr))
            self._wait_for_ask("0x31 address failed")
            
            """ send the number of bytes to be written.
                note: this number is the real sent (number -1) 
                for instance: when you are goint to send 100 bytes, here the number to be written is 100-1 = 99
            """
            lng_int = (len(data)-1) & 0xFF
            lng_hex = int_to_hex(lng_int)
            self.sp.write(lng_hex)  
            
            crc_int = lng_int           # crc_int is the first number/data for crc calculation, crc_int is being prepared for later crc calculating 

            for c_int in data:
                crc_int = crc_int ^ c_int
                c_hex = int_to_hex(c_int)
                self.sp.write(c_hex)                  # STEVEN chr(c) ---> c

            crc_hex = int_to_hex(crc_int)
            self.sp.write(crc_hex)                    # STEVEN chr(crc) ---> crc
            print("crc_hex: %s" % crc_hex) 

            self._wait_for_ask("0x31 programming failed")
            mdebug("    Write memory done")
        else:
            raise CmdException("Write memory (0x31) failed")


    def cmdEraseMemory(self, sectors = None):
        if self.extended_erase:
            return cmd.cmdExtendedEraseMemory_original()

        if self.cmdGeneric(0x43):
            mdebug("*** Erase memory command")
            if sectors is None:
                # Global erase
                self.sp.write(chr(0xFF))
                self.sp.write(chr(0x00))
            else:
                # Sectors erase
                self.sp.write(chr((len(sectors)-1) & 0xFF))
                crc = 0xFF
                for c in sectors:
                    crc = crc ^ c
                    self.sp.write(chr(c))
                self.sp.write(chr(crc))
            self._wait_for_ask("0x43 erasing failed")
            mdebug("    Erase memory done")
        else:
            raise CmdException("Erase memory (0x43) failed")

    def cmdExtendedEraseMemory_original(self):
        #if self.cmdGeneric(0x44):          # masked by steven
        self.sp.write(b'\x44')            # added by steven
        self.sp.write(b'\xBB')            # added by steven Control byte
        return_value = self._wait_for_ask('\x44')  # added by steven
        if return_value:                             # added by steven
            mdebug("*** Extended Erase memory command")
            # Global mass erase
            self.sp.write(chr(0xFF))            # need to check
            self.sp.write(chr(0xFF))
            # Checksum
            self.sp.write(chr(0x00))
            tmp = self.sp.timeout
            self.sp.timeout = 30
            print("Extended erase (0x44), this can take ten seconds or more")
            self._wait_for_ask("0x44 erasing failed")
            self.sp.timeout = tmp
            mdebug("    Extended Erase memory done")
        else:
            raise CmdException("Extended Erase memory (0x44) failed")

    def cmdExtendedEraseMemory(self):
        if self.cmdGeneric(0x44):          # masked by steven
            mdebug("*** Extended Erase memory command")
            # Global mass erase
            # Section 7 erase
            self.sp.write(int_to_hex(0x00))            # need to check
            self.sp.write(int_to_hex(0x00)) 
            self.sp.write(int_to_hex(0x00)) 
            self.sp.write(int_to_hex(0x07)) 
            # Checksum
            self.sp.write(int_to_hex(0x07)) 
            tmp = self.sp.timeout
            self.sp.timeout = 30
            print("Extended erase (0x44), this can take ten seconds or more")
            self._wait_for_ask("0x44 erasing failed")
            self.sp.timeout = tmp
            mdebug("    Extended Erase memory done")
        else:
            raise CmdException("Extended Erase memory (0x44) failed")

    def cmdWriteProtect(self, sectors):
        if self.cmdGeneric(0x63):
            mdebug("*** Write protect command")
            self.sp.write(chr((len(sectors)-1) & 0xFF))
            crc = 0xFF
            for c in sectors:
                crc = crc ^ c
                self.sp.write(chr(c))
            self.sp.write(chr(crc))
            self._wait_for_ask("0x63 write protect failed")
            mdebug("    Write protect done")
        else:
            raise CmdException("Write Protect memory (0x63) failed")

    def cmdWriteUnprotect(self):
        if self.cmdGeneric(0x73):
            mdebug("*** Write Unprotect command")
            self._wait_for_ask("0x73 write unprotect failed")
            self._wait_for_ask("0x73 write unprotect 2 failed")
            mdebug("    Write Unprotect done")
        else:
            raise CmdException("Write Unprotect (0x73) failed")

    def cmdReadoutProtect(self):
        if self.cmdGeneric(0x82):
            mdebug("*** Readout protect command")
            self._wait_for_ask("0x82 readout protect failed")
            self._wait_for_ask("0x82 readout protect 2 failed")
            mdebug("    Read protect done")
        else:
            raise CmdException("Readout protect (0x82) failed")

    def cmdReadoutUnprotect(self):
        if self.cmdGeneric(0x92):
            mdebug("*** Readout Unprotect command")
            self._wait_for_ask("0x92 readout unprotect failed")
            self._wait_for_ask("0x92 readout unprotect 2 failed")
            mdebug("    Read Unprotect done")
        else:
            raise CmdException("Readout unprotect (0x92) failed")


# Complex commands section

    def readMemory(self, addr, lng):
        data_bytearray_sum = bytearray()
        print(type(data_bytearray_sum))
        while lng > 256:
            mdebug("Read %(len)d bytes at 0x%(addr)X" % {'addr': addr, 'len': 256})
            data_bytes = self.cmdReadMemory(addr, 256)
            data_bytearray = bytearray(data_bytes) 
            data_bytearray_sum.extend(data_bytearray)
            addr = addr + 256
            lng = lng - 256
               
        mdebug("Read %(len)d bytes at 0x%(addr)X" % {'addr': addr, 'len': lng})
        data_bytes = self.cmdReadMemory(addr, lng)
        data_bytearray = bytearray(data_bytes) 
        data_bytearray_sum.extend(data_bytearray)
        data_bytes_return = bytes(data_bytearray_sum)
        return data_bytes_return

    def writeMemory(self, addr, data):      # decompose the data into pages 
        lng = len(data)
        offs = 0
        while lng > 256:
            mdebug("Write %(len)d bytes at 0x%(addr)X" % {'addr': addr, 'len': 256})    # steven moved
            self.cmdWriteMemory(addr, data[offs:offs+256])
            offs = offs + 256
            addr = addr + 256
            lng = lng - 256

        if lng > 0:     #steven added
            mdebug("Write %(len)d bytes at 0x%(addr)X" % {'addr': addr, 'len': lng})     # 256 -> len
            self.cmdWriteMemory(addr, data[offs:offs+lng])

def usage():
    print(sys.argv[0])

def int_to_hex(i):
        if(0<=i<16):
            temp1 = i%16
            if temp1<10:
                pass
            if temp1 ==10:
                temp1 = 'a'
            if temp1 ==11:
                temp1 = 'b'
            if temp1 ==12:
                temp1 = 'c'
            if temp1 ==13:
                temp1 = 'd'
            if temp1 ==14:
                temp1 = 'e'
            if temp1 ==15:
                temp1 = 'f'

            i_str1 = str(temp1)
            i_int_pad1 = i_str1.zfill(2)
            i_binary1 = bytes(i_int_pad1, 'ascii')
            i_hex = binascii.unhexlify(i_binary1)
            return i_hex
            #list.append(i_hex)

        elif (16<= i <256):
            #i_original = i
            temp = i//16
            if temp <=9:
                pass
            if temp ==10:
                temp = 'a'
            if temp ==11:
                temp = 'b'
            if temp ==12:
                temp = 'c'
            if temp ==13:
                temp = 'd'
            if temp ==14:
                temp = 'e'
            if temp ==15:
                temp = 'f'
            i_int_1 = temp

            temp = i%16
            if temp <=9:
                pass
            if temp ==10:
                temp = 'a'
            if temp ==11:
                temp = 'b'
            if temp ==12:
                temp = 'c'
            if temp ==13:
                temp = 'd'
            if temp ==14:
                temp = 'e'
            if temp ==15:
                temp = 'f'
            i_int_0 = temp
            
            i_str_1 = str(i_int_1)
            i_str_0 = str(i_int_0)
            i_str = i_str_1 + i_str_0
             
            i_binary = bytearray(i_str, 'ascii')
            i_hex = binascii.unhexlify(i_binary)
            return i_hex



if __name__ == "__main__":
    
    conf = {
            'port': 'COM10',
            'baud': 57600,              # original 115200 
            #'address': 0x0807F800,      # original 0x0800,0000
            'address': 0x0807C010,      # original 0x0800,0000
            'erase': 0,
            'write': 0,
            'verify': 0,
            'read': 0,
            'go_addr':-1,
    }

    
    conf['read'] = 1
    conf['erase'] = 1
    conf['write'] = 1
    conf['verify'] = 1

    cmd = CommandInterface()
    cmd.open(conf['port'], conf['baud'])
    mdebug("Open port %(port)s, baud %(baud)d" % {'port':conf['port'], 'baud':conf['baud']})
    try:
        try:
            cmd.initChip()
        except Exception as exception :
            print(exception.__class__.__name__)
            print("Can't init. Ensure that BOOT0 is enabled and reset device")


        bootversion = cmd.cmdGet()
        mdebug("Bootloader version %X" % bootversion)

#        id = cmd.cmdGetID()
#        mdebug("Chip id: 0x%x (%s)" % (id, chip_ids.get(id, "Unknown")))
#    cmd.cmdGetVersion()
#    cmd.cmdGetID()
#    cmd.cmdReadoutUnprotect()
#    cmd.cmdWriteUnprotect()
#    cmd.cmdWriteProtect([0, 1])

        if (conf['write'] or conf['verify']):
            bin_file = open('user_app.bin','rb')
            data = bin_file.read()

        if conf['erase']:
            cmd.cmdExtendedEraseMemory()   #becasue steven's projec is for STM32F411 chip, 

        if conf['write']:
            cmd.writeMemory(conf['address'], data)

        if conf['verify']:
            verify = cmd.readMemory(conf['address'], len(data))
            if(data == verify):
                print( "Verification OK")
            else:
                print( "Verification FAILED")
                print( str(len(data)) + ' vs ' + str(len(verify)))
                for i in range(0, len(data)):
                    if data[i] != verify[i]:
                        print( hex(i) + ': ' + hex(data[i]) + ' vs ' + hex(verify[i]))

        if not conf['write'] and conf['read']:
            rdata = cmd.readMemory(conf['address'], conf['len'])
            #file(args[0], 'wb').write(''.join(map(chr,rdata)))
            bin_file = open('user_app.bin','wb')
            bin_file.write(''.join(map(chr,rdata)))

        if conf['go_addr'] != -1:
            cmd.cmdGo(conf['go_addr'])

    finally:
        cmd.releaseChip()
