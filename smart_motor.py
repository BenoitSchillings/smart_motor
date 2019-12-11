import socket
import sys
from parse import *


import time
import serial
import datetime
import ephem
import threading

class Smartmotor:
    def __init__(self, a_port):
        self.atEnd = False
        self.setupSerialConnection(a_port)
        self.base_time = time.clock()
        self.raw_speed = 0

    def setupSerialConnection(self, a_port):
        self.ser = serial.Serial(port=a_port,
                                 baudrate=9600,
                                 bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 timeout=2)
        if (self.ser.isOpen() == False):
            self.ser.open()
        self.writeser('ECHO_OFF ')
        self.writeser('ZS ')
        self.writeser('MP ')
        self.writeser('MDS ')
        #self.writeser('EIGN(2) ')
        #self.writeser('EIGN(3) ')
        #self.writeser('PID1 ')
        self.writeser('MFR ')
        #self.writeser('O=0 ')
        #ignore = self.getString()
       
 
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
        self.writeser('G ')

    def Velocity(self):
        self.writeser('MV ')
        self.Go()

    def Position(self):
        self.writeser('MP ')
        self.Go()

    def Speed(self, speed):
        self.target_speed = speed
        self.writeser('VT=%d ' % (speed))
        self.raw_speed = int(speed)
        time.sleep(0.04)

    def SetPos(self, pos):
        self.writeser('O=%d ' % pos)

    def SpeedAdjust(self):
        cur_time = time.clock()
        dt = cur_time - self.base_time
        dt = int(dt + 0.5)
        dt = dt % 50

        ratio = self.target_speed % 1

        ratio = int(ratio * 50.0 + 0.5)
        speed0 = int(self.target_speed)
        if (dt < ratio):
            if (self.raw_speed != (speed0+1)):
                self.writeser('VT=%d ' % (speed0+1)) 
                self.raw_speed = speed0+1
                self.Go() 
        if (dt > ratio):
            if (self.raw_speed != (speed0)):
                self.writeser('VT=%d ' % (speed0)) 
                self.raw_speed = speed0
                self.Go() 
        


    def Acceleration(self, acc):
        self.writeser('AT=%d ' % acc)
        time.sleep(0.04)

    def Target(self, pos):
        self.writeser('PT=%d ' % pos)
        time.sleep(0.04)


    def writeser(self, string):
        #print("write ", string)
        self.ser.write(string.encode())

    def getString(self):
        currentString = ''
        currentChar = 0
        while (currentChar!=b'\x20' and currentChar!=b'\n' and currentChar!=b'\r'):
            currentChar = self.ser.read()
            currentString += currentChar.decode("utf-8", "ignore")
            
        return currentString

    def getPosition(self):
        self.writeser('RP ')

        string = self.getString()
 
        position = int(string)
        return(position)

    def getSpeed(self):
        self.writeser('RV ')

        string = self.getString()
 
        position = int(string)
        return(position)

    def motor_steps(self):                      #number of step for one full rotation
        return 20000.0
    
    def position_to_rotation(self, value):
        return(value / self.motor_steps())

    def rotation_to_position(self, value):
        return(value * self.motor_steps())

    def calc_rps(self):                         #speed to get 1 rotation per second
        mult = self.motor_steps() / 6208.8      #master constant for rotation speed
        rate = 100000.0 * mult
        return rate

#1 motor rotation = 20000 count on encoder
#speed of 100000 is encoder count of 6211 per second

