#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import random
from unicorn import *
from unicorn.arm_const import *
from capstone import *
import argparse
import codecs
import binascii
import time
import os.path

uc = Uc(UC_ARCH_ARM, UC_MODE_ARM | UC_MODE_THUMB | UC_MODE_MCLASS)
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_THUMB | CS_MODE_MCLASS)

peri_init = {}
peri_bits = {}
peri_type = {}
peri_banding = {}
set_bits = []

flag = 0

before_value = 0
before_addr = 0

def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--firmware', type=str, help="firmware binary")
    parser.add_argument('--base_addr', type=int, default=0x8000000, help="the base address of firmware")

    return parser.parse_args()

def bytes_to_int(inputs):
    result = 0
    inputs = inputs[::-1]
    for b in inputs:
        result = result * 256 + int (b)

    return long(result)

def int_to_hex_rev(value):
    value = int(value)
    hex_str = '%08x' %value
    str_to_convert = hex_str[6:8] + hex_str[4:6] + hex_str[2:4] + hex_str[0:2]
    return codecs.decode(str_to_convert, "hex")


def debug_instruction(uc, address, size, user_data):
    global flag
    global global_base_addr

    mem = uc.mem_read(address, size)

    if flag == 1:
        flag = 0
        global set_bits

        global before_value
        global before_addr

        uc.mem_write(before_addr, int_to_hex_rev(before_value))

        for addr_dict in set_bits:
            for addr in addr_dict:
                value = addr_dict[addr]
                prev_value = bytes_to_int(uc.mem_read(addr, 4))
                new_value = value
                uc.mem_write(addr, int_to_hex_rev(new_value))


def mem_read(uc, access, address, size, value, data):
    mem_value = bytes_to_int(uc.mem_read(address, 4))

    if address >= 0x40000000:
        if address not in peri_init:
            output = '%x' %address
            fp = open('model/add_regs.txt', 'w')
            fp.write(output)
            fp.close()
            os._exit(1)

            return
    return

def pre_mem_write(uc, access, address, size, value, data):
    if address >= 0x40000000:
        global flag
        global peri_banding
        global set_bits

        flag = 1
        if address not in peri_init:
            output = '%x' %address
            fp = open('model/add_regs.txt', 'w')
            fp.write(output)
            fp.write("\n")
            fp.write(str(value))
            fp.close()
            os._exit(1)

            return

        global before_addr
        global before_value
        before_addr = address
        before_value = bytes_to_int(uc.mem_read(address, 4))
        if address in peri_banding:
            band_list = peri_banding[address]

            for add_dict in band_list:
                for add_value in add_dict:
                    if add_value == value:
                        write_fp = open('model/peri_write.txt', 'a')
                        output = '%x' %address
                        write_fp.write(output)
                        write_fp.write("\n")
                        write_fp.write(str(value))
                        write_fp.write("\n")
                        write_fp.close()


                        set_bits = add_dict[add_value]
                        return


        output = '%x' %address
        fp = open('model/add_regs.txt', 'w')
        fp.write(output)
        fp.write("\n")
        fp.write(str(value))
        fp.close()
        os._exit(1)

        return

    return

def init_peri_reg():
    global peri_init

    for addr in peri_init:
        init_value = peri_init[addr]
        uc.mem_write(addr, int_to_hex_rev(init_value))
    return


def read_peripheral_model():
    global peri_init #= {}
    global peri_banding #= {}


    if (os.path.isfile('model/result.txt') == False):
        return

    fp = open('model/result.txt', 'r')

    while True:
        line = fp.readline()

        if not line:
            break

        addr = (line.split())[1]
        addr = int(addr, 0)

        line = fp.readline()
        init_value = (line.split())[2]
        init_value = int(init_value, 0)

        if addr not in peri_init:
            peri_init[addr] = init_value


        line = fp.readline()
        if line == "\n":
            continue
        elif not line:
            break

        add_value = line.strip()
        add_value = int(add_value)
        bit_band = []
        sub_banding = {}
        while True:
            band_addr = fp.readline()
            if band_addr == '\n':
                break

            addr_and_value = band_addr.strip().split()
            band_addr = addr_and_value[0]
            final_val = int(addr_and_value[1])
            band_addr = int(band_addr, 0)
            value_pair = {}
            value_pair[band_addr] = final_val
            bit_band.append(value_pair)

        sub_banding[add_value] = bit_band

        if peri_banding.has_key(addr) == True:
            peri_banding[addr].append(sub_banding)
        else:
            peri_banding[addr] = []
            peri_banding[addr].append(sub_banding)


def map_elf_memory(filename):
    CODE_ADDR = 0x0
    STACK_SIZE = 0x8000

    CODE = open(filename).read()

    fp = open(filename, 'rb')

    stack_addr_rev = fp.read(4)
    entry_addr_rev = fp.read(4)

    stack_addr = ""
    entry_addr = ""

    for i in range(0, len(stack_addr_rev)):
        stack_addr += stack_addr_rev[3-i]
        entry_addr += entry_addr_rev[3-i]
    fp.close()

    START_ADDR = int(entry_addr.encode("hex"), 16)
    STACK_ADDR = int(stack_addr.encode("hex"), 16)


    SIZE = 0xfffff000
    uc.mem_map(0x0, SIZE)
    uc.mem_map(0xfffff000, 0x1000)

    FFlist = "FF" * 0x80000
    FFlist = codecs.decode(FFlist, "hex")
    uc.mem_write(0x0, FFlist)

    uc.mem_write(0x8000000, CODE)
    uc.reg_write(UC_ARM_REG_SP, STACK_ADDR)

    uc.hook_add(UC_HOOK_CODE, debug_instruction)
    uc.hook_add(UC_HOOK_MEM_WRITE, pre_mem_write)
    uc.hook_add(UC_HOOK_MEM_READ, mem_read)
    return START_ADDR

def main():
    args = arg_parser()

    read_peripheral_model()

    if (os.path.isfile('model/peri_write.txt') == True):
        os.remove('model/peri_write.txt')
    fp = open('model/peri_write.txt','w')
    fp.close()

    global peri_init #= {}
    global peri_bits #= {}
    global peri_type #= []
    global peri_banding #= {}
    global global_base_addr
    global_base_addr = args.base_addr
    start_addr = map_elf_memory(args.firmware)

    init_peri_reg()


    uc.emu_start(start_addr | 1, 0, 0, count=100000)

if __name__ == "__main__":
    main()
