#!/usr/bin/env python
# started/forked from the code of Paul Milliken at
# https://github.com/paulmilliken/smart_motor

import time
import serial

class Smartmotor:
    def __init__(self):
        self.atEnd = False
        self.setupSerialConnection()

    def setupSerialConnection(self):
        self.ser = serial.Serial(port='/dev/ttyS0', baudrate=9600,
                bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE, timeout=120)
        try:
            self.openSerialPort()
        except:
            print('Could not open serial port')

    def openSerialPort(self):
        try:
            self.ser.open()
        except:
            print('Error: failed to open serial connection to smartmotor')

    def closeSerialPort(self):
        try:
            self.ser.close()
        except:
            print('Warning: failed to close serial connection to smartmotor')

    def isConnected(self):
        '''Check if serial connection to smartmotor is alive'''
        if self.ser.isOpen():
            print('Serial port is open')
            return(True)
        else:
            print('Serial port is not open')
            return(False)

    def Go(self):
        self.ser.write('G ')

    def Speed(self, speed):
        self.ser.write('VT=%d ', speed)
        time.sleep(0.1)

    def Acceleration(self, acc):
        self.ser.write('ADT=%d ', acc)
        time.sleep(0.1)

    def Target(self, pos):
        self.ser.write('PRT=%d ', pos)
        time.sleep(0.1)


    def getPosition(self):
        self.ser.write('RPA ')
        currentString = ''
        currentChar = None
        while (currentChar!=' ' and currentChar!='\n' and currentChar!='\r'):
            currentChar = self.ser.read()
            currentString += currentChar
        position = int(currentString)
        return(position)

if __name__ == '__main__':
    motor = Smartmotor()
    motor.Speed(1000)
    motor.Acceleration(20)
    motor.Target(10000)
    motor.Go()
    print(motor.getPosition())
    time.sleep(2)
    print(motor.getPosition())
    motor.closeSerialPort()
