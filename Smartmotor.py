#!/usr/bin/env python
# started/forked from the code of Paul Milliken at
# https://github.com/paulmilliken/smart_motor

import time
import serial

class Smartmotor:
    def __init__(self):
        self.atEnd = False
        self.setupSerialConnection()
        self.endPosition = 675000 # 764000=6 metres, 675000 is start of board

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

    def doScan(self):
        '''Send commands to smartmotor to move board through scanner'''
        print('Starting scan')
        self.atEnd = False
        self.ser.write('VT=60000 ') # Joe90 target speed normally 300000
        time.sleep(0.1)
        self.ser.write('PT=%d ' % self.endPosition)
        time.sleep(0.1)
        self.ser.write('G ') # Go!

    def getStartPosition(self):
        '''Allow for a start position in front of the limit switch to save 
        collecting images before the board is under the camera'''
        print('Preparing to preposition')
        startPosition = 0
        rospy.loginfo("Start position is %d" % startPosition)
        if (startPosition<0):
            startPosition = 0
        elif (startPosition>400000):
            startPosition = 400000
        return(startPosition)
        
    def prePosition(self):
        '''Send commands to smartmotor to move board through scanner'''
        print('Starting prepositioning')
        
        self.atEnd = False
        self.ser.write('VT=600000 ') # Joe90 target speed normally 300000
        time.sleep(0.1)
        startPosition = self.getStartPosition()
        self.ser.write('PT=%d ' % startPosition) # 764000 = 6 metres
        time.sleep(0.1)
        self.ser.write('G ') # Go!

    def returnToStartPosition(self):
        '''C30 is preprogrammed into the smartmotor to return to origin'''
        
        self.atEnd = False
        self.ser.write('GOSUB(30) ')

    def home(self):
        '''C10 is preprogrammed into the smartmotor to find the home limit
        switch'''
        
        self.atEnd = False
        self.ser.write('GOSUB(10) ')
        return()

    def getDisplacement(self):
        self.ser.write('RPA ')
        currentString = ''
        currentChar = None
        while (currentChar!=' ' and currentChar!='\n' and currentChar!='\r'):
            currentChar = self.ser.read()
            currentString += currentChar
        displacement = int(currentString)
        if ((self.endPosition - displacement)<100):
            self.atEnd = True
        return(SmartmotorDisplacementResponse(displacement))

    def runAll(self):
        self.prePosition()
        time.sleep(10.0) # allow time to get to start_position
        self.doScan()
        while(True):
            if (self.atEnd==True):
                break
        time.sleep(4.0)
        self.returnToStartPosition()

if __name__ == '__main__':
    motor = Smartmotor()
