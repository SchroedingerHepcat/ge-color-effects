#! /usr/bin/env python

nHigh = 8
nLong = 17
for i in range(2**(nLong-3)):
    # Check if it has 8 ones
    nOnes = 0
    for j in range(nLong):
        nOnes += (i & (1<<j)) > 0
        
    if nOnes == 8:
        s = bin(i)[2:]
        s = (nLong - len(s))*"0" + s
        print(s + 'e')
        print(s + 'f')
