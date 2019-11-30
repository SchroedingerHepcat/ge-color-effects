#! /usr/bin/env python

import csv
import numpy
import sys

def readtrace(filename):
    samples = []
    with open(filename) as f:
        reader = csv.reader(f)
        version = float(reader.__next__()[1])
        fSampling = float(reader.__next__()[1])
        nSamples = int(reader.__next__()[1])
        nRecords = int(reader.__next__()[1])
        timeStamp = reader.__next__()[1]
        tOffset = float(reader.__next__()[1])
        triggerPos = float(reader.__next__()[1])
        fastFrameId = int(reader.__next__()[1])
        idInFrastFrame = int(reader.__next__()[1])
        TotalInFastFrame = int(reader.__next__()[1])

        for row in reader:
            sampleI = float(row[0])
            sampleQ = float(row[1])
            samples.append(complex(real=sampleI, imag=sampleQ))

    return samples, fSampling

def estimateNoise(data):
    return numpy.median(magSqData) * 1.4


def detectPulses(data, noise, threshold):
    startIndices = []
    stopIndices = []
    state = 0
    for i, sample in enumerate(data):
        if state == 0 and db(sample/noise) > threshold:
            startIndices.append(i)
            state = 1
        elif state == 1 and db(sample/noise) < threshold:
            stopIndices.append(i-1)
            state = 0

    return startIndices, stopIndices

def detectRisingEdge(data, noise, threshold):
    pass

def decodeMessage(pulseStarts, pulseStops, bitlength, fs):
    msg = []
    for i in range(len(pulseStarts)):
        tStart = pulseStarts[i] / fs
        tStop = pulseStops[i] / fs
        for j in range(int(numpy.rint((tStop - tStart) / bitlength))):
            msg.append(1)
        if i + 1 < len(pulseStarts):
            tStartNext = pulseStarts[i+1] / fs
            for j in range(int(numpy.rint((tStartNext - tStop) / bitlength))):
                msg.append(0)

    # Add zeroes to the end of the string to pack it to even bytes
    if len(msg) % 8 > 0:
        for i in range(8 - (len(msg) % 8)):
            msg.append(0)

    return msg


def printMsg(msg):
    cnt = 0
    lastbit = msg[0]
    for bit in msg:
        if bit == lastbit:
            cnt += 1
        else:
            print(lastbit, ": ", cnt)
            cnt = 1
            lastbit = bit
    print(lastbit, ": ", cnt)


def interpolateCrossing(data, i, threshold):
    iInterpolated = i - 1 + (threshold - data[i-1]) / (data[i] - data[i-1])
    print(i, iInterpolated)
    return iInterpolated


def measureBitLength(pulseStarts, pulseStops, fs, initialEstimate=None):
    # Minimize the error of the bit rate times the multiple of bits between each
    # transition
    pulseWidths = [(iStop - iStart) / fs
                   for iStart, iStop in zip(pulseStarts, pulseStops)
                  ]
    if not initialEstimate:
        estBitRate = numpy.min(pulseWidths)
        print("Initial Estimate: ", estBitRate)
    else:
        estBitRate = initialEstimate
    
    lastEstimate = estBitRate
    lastResidual = 1e999
    shiftRate = 0.1
    goodEnough = False
    while not goodEnough:
        l2residual = 0
        for i in range(len(pulseStarts)):
            tStart = pulseStarts[i] / fs
            tStop = pulseStops[i] / fs
            nBits = (tStop - tStart) / estBitRate
            l2residual = pow(nBits - numpy.rint(nBits), 2)

            if i + 1 < len(pulseStarts):
                tStartNext = pulseStarts[i+1] / fs
                nBits = (tStartNext - tStop) / estBitRate
                l2residual = pow(nBits - numpy.rint(nBits), 2)

        if l2residual > lastResidual:
            estBitRate = lastEstimate
            l2residual = lastResidual
            shiftRate = shiftRate*0.1
        elif abs(l2residual - lastResidual) < 0.0001:
            goodEnough = True

        if not goodEnough:
            lastEstimate = estBitRate
            lastResidual = l2residual
            estBitRate = estBitRate * (1+shiftRate)


    return estBitRate, l2residual


def removePreamble(msg):
    preamble = True
    cnt = 0
    nRemoved = 0
    while cnt < 33:
        if msg[0] == 0.:
            cnt += 1
        else:
            cnt = 0
        del msg[0]
        nRemoved += 1

    while msg[0] == 0.:
        del msg[0]
        nRemoved += 1

    if msg[1] == 0:
        msg.insert(0, 0)
        msg.insert(0, 0)
        msg.insert(0, 0)
        nRemoved -= 3

    return msg 

def decodeSymbols(msg):
    preamble = True
    cnt = 0
    nRemoved = 0
    while cnt < 33:
        if msg[0] == 0.:
            cnt += 1
        else:
            cnt = 0
        del msg[0]
        nRemoved += 1

    while msg[0] == 0.:
        del msg[0]
        nRemoved += 1

    if msg[1] == 0:
        msg.insert(0, 0)
        msg.insert(0, 0)
        msg.insert(0, 0)
        nRemoved -= 3

    #print("nRemoved: ", nRemoved)
    #print(msg)

    symbols = []
    while len(msg) > 3:
        if msg[0] == 1 and msg[1] == 1 and msg[2] == 1 and msg[3] == 0:
            symbols.append(1)
            del msg[3]
            del msg[2]
            del msg[1]
            del msg[0]
        elif msg[0] == 1 and msg[1] == 0 and msg[2] == 0 and msg[3] == 0:
            del msg[3]
            del msg[2]
            del msg[1]
            del msg[0]
            symbols.append(0)
        else:
            break

    print("Remaining msg: ", msg)
    return symbols

def listToBinaryString(cList):
    s = ""
    for c in cList:
        s = s + str(c)
    return s


def printSymbols(symbols):
    for symbol in symbols:
        print(symbol, end='')


def printBinaryStringAsHex(s):
    h = ''
    i = 0
    while i < len(s):
        #print()
        #print(s[i:i+8])
        #print(hex(int(s[i:i+8],2)))
        h += hex(int(s[i:i+8], 2)) + " "
        i += 8


    #print()
    print(h)


def db(x):
    return 10*numpy.log10(x)

if __name__ == "__main__":
    data, fs = numpy.array(readtrace(sys.argv[1]))
    magSqData = numpy.array([s.real * s.real + s.imag * s.imag
                            for s in data]
                           )

    bne = estimateNoise(magSqData)  
    #print("BNE: ", bne)

    maxValue = numpy.max(magSqData)
    maxSNR = maxValue/bne
    #print("SNR: ", db(maxSNR))

    threshold = db(maxSNR) - 10

    pulseStarts, pulseStops = detectPulses(magSqData, bne, threshold)
    
    #snrData = [s / bne for s in magSqData]
    #linThreshold = pow(10,(threshold / 10))
    #pulseStarts = [interpolateCrossing(snrData, start, linThreshold)
    #               for start in pulseStarts
    #              ]
    #pulseStops = [interpolateCrossing(snrData, stop, linThreshold)
    #              for stop in pulseStops
    #             ]

    pulseWidths = [(pulse[1] - pulse[0]) / fs
                   for pulse in zip(pulseStarts, pulseStops)
                  ]

    #for pw in pulseWidths:
    #    print(pw)

    #print("f_s: ",1/fs)
    #print()
    #bitlength = numpy.min(pulseWidths)
    bitlength = 1./8.8e3
    #bitlength, residual = measureBitLength(pulseStarts
                                          #,pulseStops
                                          #,fs
                                          #,initialEstimate=0.00011245
                                          #)
    #print("Bitlength: ", bitlength)
    #print("L2 Residual: ", residual)
    #print("Bit Rate: ", 1/bitlength)
    #print("Sample Length: ", 1/fs)
    #print()

    msg = decodeMessage(pulseStarts, pulseStops, bitlength, fs)
    msg = removePreamble(msg)
    msgBinaryStr = listToBinaryString(msg)
    #print(msgBinaryStr)
    #print()
    printBinaryStringAsHex(msgBinaryStr)

    #printSymbols(msg)
    #print(msg)
    #printMsg(msg)

    #print()
    #symbols = decodeSymbols(msg)

    #print()
    #print(symbols)
    #print()
    #printSymbols(symbols)

    #import pdb
    #pdb.set_trace()

    #import matplotlib.pyplot as plotter

    #times = [i / fs for i,s in enumerate(magSqData)]
    #plotter.figure()
    #plotter.plot(times, [db(s) for s in magSqData], 'b.-')
    #plotter.plot(times, [threshold + db(bne) for s in magSqData])
    #plotter.plot([i/fs for i in pulseStarts], [threshold + db(bne) for s in pulseStarts], 'x')
    #plotter.plot([i/fs for i in pulseStops], [threshold + db(bne) for s in pulseStops], 'o')
    #plotter.show()
