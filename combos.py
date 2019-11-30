#! /usr/bin/env python

from bitarray import bitarray

for i in range(2**16):
    a = bitarray(bin(i))
    print(bin(i))
