#! /usr/bin/env python

import serial
import time

arduinoSerial = '/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_7553335373735171D121-if00'
radioSerial = '/dev/serial/by-id/usb-Silicon_Labs_J-Link_Pro_OB_000440137542-if00'

outFile = 'validCodes.txt'
threshold = 200

# Arduino commands
# r for reset
# g for get

def getLightSensor(sensor):
    n = sensor.write(b'g')
    value = int(sensor.read_until())
    return value

def resetLightSensor(sensor):
    n = sensor.write(b'r')

def sendRadioCode(code, radio):
    radio.write(b'custom ' + code + b'\n')
    pass

def generateCodes(nHigh, nLong):
    for i in range(2**(nLong-3)):
        # Check if it has 8 ones
        nOnes = 0
        for j in range(nLong):
            nOnes += (i & (1<<j)) > 0
            
        if nOnes == 8:
            s = bin(i)[2:]
            s = (nLong - len(s))*"0" + s
            yield (s + 'e')
            yield (s + 'f')

if __name__ == '__main__':
    inCodeFile = open('validCodes.txt', 'r')
    radio = serial.Serial(radioSerial, 115200) 
    sensor = serial.Serial(arduinoSerial, 9600) 
    time.sleep(2)

    off   = b'000101000110101110'
    red   = b'00000000011111111e'
    green = b'00000000111111110e'
    blue  = b'00000001111111100e'
    flashing = b'00001100011100111e'
    fading = b'00000011111111000e'

    lines = inCodeFile.readlines()
    for code in lines:
        # Change color
        print('Setting code: ', code)
        sendRadioCode(bytearray(code.encode('utf')), radio)
        time.sleep(5)
