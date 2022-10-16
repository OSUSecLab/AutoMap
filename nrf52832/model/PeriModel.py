#!/usr/bin/env python3

import argparse
import os
import sys
import random
import codecs
import binascii
import subprocess
import time

done_list = []
flag = -1

peri_addr_range = []
peri_mem_map_idx = []

def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--peri_file', type=str, default="peri_regs.txt", help="file for the list of peripheral registers address")
    parser.add_argument('--bin_file', type=str, help="firmware binary file name")

    return parser.parse_args()

def read_memory(base_addr, length, filetype):
    if os.path.exists(filetype):
        os.remove(filetype)
    gdb.execute("set logging file " + filetype)
    gdb.execute("set logging on")
    idx = 0
    while (idx < length):
        gdb.execute("x /4x " + str(hex(base_addr + idx)))
        idx = idx + 16

    gdb.execute("set logging off")
    fp = open(filetype, 'r')
    lines = fp.readlines()
    result = []
    for line in lines:
        idx = 1
        for j in range(0, 4):
            addr = line.split()[idx]
            addr_val = int(addr, 16)
            for i in range(0, 4):
                result.append(addr_val % 256)
                addr_val = addr_val / 256
            idx = idx + 1

    return result

def init_read_memory(base_addr, length, filetype):
    if os.path.exists(filetype):
        os.remove(filetype)
    gdb.execute("set logging file " + filetype)
    gdb.execute("set logging on")
    idx = 0
    while (idx < length):
        gdb.execute("x /x " + str(hex(base_addr + idx)))
        idx = idx + 4

    gdb.execute("set logging off")
    fp = open(filetype, 'r')
    lines = fp.readlines()
    result = []
    for line in lines:
        addr = line.split()[1]
        addr_val = int(addr, 16)
        for i in range(0, 4):
            result.append(addr_val % 256)
            addr_val = addr_val / 256

    return result


def bytes_to_int(inputs):
    result = 0
    inputs = inputs[::-1]

    for b in inputs:
        result = result * 256 + ord(b)

    return long(result)

def get_peri_list(filename):
    fp = open(filename, 'r')

    addr = fp.readline()
    value = fp.readline()

    return addr, value

def stepi(count):
    for i in range(count):
        gdb.execute('stepi')

def reverse(str_val):
    temp = str_val[6:8] + str_val[4:6] + str_val[2:4] + str_val[0:2]
    return temp

def start_gdb(filename):
    input_file = 'file ' + filename
    gdb.execute(input_file)
    gdb.execute('target remote localhost:2331')
    gdb.execute('mon speed 10000')
    gdb.execute('mon flash download=1')
    gdb.execute('load')
    gdb.execute('mon reset 0')
    gdb.execute('mon reset 0')
    gdb.execute('set pagination off')
    gdb.execute('set arm force-mode thumb')
    gdb.execute('set endian little')


def build_model(peri_addr, value):

    gdb.execute('mon reset 0')

    l = gdb.inferiors()[0]

    global peri_addr_range
    global peri_mem_map_idx
    global done_list
    peri_addr = peri_addr.strip()
    peri_addr = int(peri_addr, 16)

    value = value.strip()
    value = int(value, 10)


    init_peri_val = l.read_memory(peri_addr, 4)
    init_peri_val = bytes_to_int(init_peri_val)

    ret = add_prev_peri()

    base_addr = 0x40000000
    length = 0x30000

    prev_first_mem = l.read_memory(base_addr, length)
    prev_second_mem = l.read_memory(0x50000000, 0x40000)
    prev_third_mem = l.read_memory(0xe0000000, 0x10000)
    prev_fourth_mem = l.read_memory(0xe0040000, 0x2000)
    prev_fifth_mem = l.read_memory(0xf0000000, 0x10000)
    prev_sixth_mem = l.read_memory(0xf0040000, 0x2000)

    if value < 0:
        str_val = format(4294967296 - value, '08x')
    else:
        str_val = format(value, '08x')

    str_val = reverse(str_val)
    str_val = codecs.decode(str_val, "hex")

    l.write_memory(peri_addr, str_val, 4)
    stepi(2000)

    next_first_mem = l.read_memory(base_addr, length)
    next_second_mem = l.read_memory(0x50000000, 0x40000)
    next_third_mem = l.read_memory(0xe0000000, 0x10000)
    next_fourth_mem = l.read_memory(0xe0040000, 0x2000)
    next_fifth_mem = l.read_memory(0xf0000000, 0x10000)
    next_sixth_mem = l.read_memory(0xf0040000, 0x2000)

    idx=0

    fp = open("./result.txt", 'a')
    fp.write("addr 0x%x information\n" %peri_addr)
    fp.write("initial value 0x%x\n" %init_peri_val)
    fp.write("%d\n" %value)


    idx=0
    peri_start_addr = 0x40000000
    while idx < len(prev_first_mem):
        if idx + peri_start_addr >= peri_addr and idx + peri_start_addr <= peri_addr + 3:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_first_mem[idx:idx+4])))
        elif prev_first_mem[idx:idx+4] != next_first_mem[idx:idx+4]:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_first_mem[idx:idx+4])))
        idx = idx + 4

    idx=0
    peri_start_addr = 0x50000000
    while idx < len(prev_second_mem):
        if idx + peri_start_addr >= peri_addr and idx + peri_start_addr <= peri_addr + 3:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_second_mem[idx:idx+4])))
        elif prev_second_mem[idx:idx+4] != next_second_mem[idx:idx+4]:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_second_mem[idx:idx+4])))
        idx = idx + 4

    idx=0
    peri_start_addr = 0xe0000000
    while idx < len(prev_third_mem):
        if idx + peri_start_addr >= peri_addr and idx + peri_start_addr <= peri_addr + 3:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_third_mem[idx:idx+4])))
        elif prev_third_mem[idx:idx+4] != next_third_mem[idx:idx+4]:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_third_mem[idx:idx+4])))
        idx = idx + 4

    idx=0
    peri_start_addr = 0xe0040000
    while idx < len(prev_fourth_mem):
        if idx + peri_start_addr >= peri_addr and idx + peri_start_addr <= peri_addr + 3:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_fourth_mem[idx:idx+4])))
        elif prev_fourth_mem[idx:idx+4] != next_fourth_mem[idx:idx+4]:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_fourth_mem[idx:idx+4])))
        idx = idx + 4

    idx=0
    peri_start_addr = 0xf0000000
    while idx < len(prev_fifth_mem):
        if idx + peri_start_addr >= peri_addr and idx + peri_start_addr <= peri_addr + 3:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_fifth_mem[idx:idx+4])))
        elif prev_fifth_mem[idx:idx+4] != next_fifth_mem[idx:idx+4]:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_fifth_mem[idx:idx+4])))
        idx = idx + 4

    idx=0
    peri_start_addr = 0xf0040000
    while idx < len(prev_sixth_mem):
        if idx + peri_start_addr >= peri_addr and idx + peri_start_addr <= peri_addr + 3:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_sixth_mem[idx:idx+4])))
        elif prev_sixth_mem[idx:idx+4] != next_sixth_mem[idx:idx+4]:
            fp.write("0x%x %d\n" %(idx + peri_start_addr, bytes_to_int(next_sixth_mem[idx:idx+4])))
        idx = idx + 4

    fp.write("\n")
    fp.close()


def calc_init(peri_addr):
    gdb.execute('mon reset 0')
    peri_addr = peri_addr.strip()
    peri_addr = int(peri_addr, 16)
    l = gdb.inferiors()[0]
    init_peri_val = l.read_memory(peri_addr, 4)
    init_peri_val = bytes_to_int(init_peri_val)
    fp = open("./result.txt", 'a')
    fp.write("addr 0x%x information\n" %peri_addr)
    fp.write("initial value 0x%x\n" %init_peri_val)
    fp.write("\n")

def check_cache(peri_addr, value):
    fp = open("../result.txt", 'r')

    peri_addr = int(peri_addr.strip(), 16)
    value = int(value.strip(), 10)

    while True:
        line_1 = fp.readline()

        if not line_1:
            break

        addr = (line_1.split())[1]
        addr = int(addr, 0)

        line_2 = fp.readline()
        init_value = (line_2.split())[2]
        init_value = int(init_value, 0)

        line_3 = fp.readline()
        if line_3 == "\n":
            continue
        elif not line_3:
            break

        add_value = line_3.strip()
        add_value = int(add_value)
        flag = 0
        if addr == peri_addr and value == add_value:
            flag = 1
            output = open("./result.txt", 'a')
            output.write(line_1)
            output.write(line_2)
            output.write(line_3)

        while True:
            band_addr = fp.readline()
            if flag == 1:
                output.write(band_addr)

            if band_addr == "\n":
                break

        if flag == 1:
            return 1

    return 0

def add_prev_peri():
    fp = open('./peri_write.txt', 'r')
    l = gdb.inferiors()[0]

    while True:
        line = fp.readline()

        if not line:
            break

        addr = (line.split())[0]
        addr = int(addr, 16)

        line = fp.readline()
        add_value = (line.split())[0]
        add_value = int(add_value, 10)

        if add_value < 0:
            str_val = format(4294967296 - add_value, '08x')
        else:
            str_val = format(add_value, '08x')
            str_val = reverse(str_val)
            str_val = codecs.decode(str_val, "hex")
        l.write_memory(addr, str_val, 4)
        stepi(2000)

    fp.close()
    return 1

def read_peri_range():
    global peri_addr_range
    global peri_mem_map_idx

    fp = open('/peri_ranges', 'r')
    lines = fp.readlines()

    for line in lines:
        vals = line.strip().split()
        start_addr = int(vals[0], 16)
        end_addr = int(vals[1], 16)

        addrs = [start_addr, end_addr]
        peri_addr_range.append(addrs)

        mem_idx = []
        if len(vals) > 2:
            idx = 2
            while idx < len(vals):
                mem_idx.append(int(vals[idx], 0))
                idx += 1

        peri_mem_map_idx.append(mem_idx)

    return

def main():
    bin_file = "./inf.out"

    peri_file = "./add_regs.txt"

    peri_addr, value = get_peri_list(peri_file)

    start_gdb(bin_file)

    if len(value) != 0:
        check = check_cache(peri_addr, value)
        if check == 0:
            #read_peri_range()
            build_model(peri_addr, value)
    else:
        calc_init(peri_addr)


if __name__ == "__main__":
    main()
