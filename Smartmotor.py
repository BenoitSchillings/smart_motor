#!/usr/bin/env python
# started/forked from the code of Paul Milliken at
# https://github.com/paulmilliken/smart_motor

#----------------------------------------------------------

import time
import serial
import datetime
import ephem

#----------------------------------------------------------

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

    def motor_steps(self):          #number of step for one full rotation
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

#----------------------------------------------------------



class Mount:
    def __init__(self):
        self.motor_DEC = Smartmotor('COM8')
        self.motor_RA = Smartmotor('COM9')
        self.motor_DEC.Acceleration(200)
        self.motor_RA.Acceleration(200)
        self.ephem = ephem.city('San Francisco')
        self.sky_angle = self.siderial_angle()

    def set_RA(self, ra):
        self.motor_RA.SetPos(self.ra_to_pos(ra))


    def set_DEC(self, dec):
        self.motor_DEC.SetPos(self.dec_to_pos(dec))


    def siderial_angle(self):
        self.ephem.date = datetime.datetime.now()
        return 57.29580026*self.ephem.sidereal_time()


    def RA_Rotation(self):          #angle per worm gear rotation
        return(360.0/225.0)

    def DEC_Rotation(self):         #angle per worm gear rotation
        return(360.0/225.0)

    def RA_rate(self, rate=15.0):    #motion rate (in arcsec per second)
        unity_rate_0 = self.motor_RA.calc_rps()
        unity_rate = self.RA_Rotation() * 3600.0 #this would be one RPS arcsec rate
        divider = rate / unity_rate
        self.motor_RA.Speed(unity_rate_0 * divider)
        self.motor_RA.Go()

    def DEC_rate(self, rate=0.0):    #motion rate (in arcsec per second)
        unity_rate_0 = self.motor_DEC.calc_rps()
        unity_rate = self.DEC_Rotation() * 3600.0 #this would be one RPS arcsec rate
        divider = rate / unity_rate
        self.motor_DEC.Speed(unity_rate_0 * divider)
        self.motor_DEC.Go()


    def ra_to_pos(self, ra):                #map RA value (0..360) to target encoder value
        delta_RA = self.siderial_angle()              #second for the reference RA
        ra = ra + delta_RA
        ra = ra % 360

        ra = ra / self.RA_Rotation()
        ra = self.motor_RA.rotation_to_position(ra)
        
        return ra      

    def dec_to_pos(self, dec):              #map DEC value (-90..90) to target encoder value
        dec = dec / self.DEC_Rotation()
        dec = self.motor_DEC.rotation_to_position(dec)
        return dec


    def pos_to_RA(self, pos):               # map encoder to RA
        pos = self.motor_RA.position_to_rotation(pos)
        pos = pos * self.RA_Rotation()
        delta_RA = self.siderial_angle()
        ra = pos - delta_RA
        ra = ra % 360

        return ra       

    def pos_to_DEC(self, pos):          #map encoder to DEC
        pos = self.motor_DEC.position_to_rotation(pos)
        pos = pos * self.DEC_Rotation()
        
        return pos         


    def target_pos(self, ra, dec):
        vra = self.ra_to_pos(ra)
        vdec = self.dec_to_pos(dec)
        self.motor_DEC.Target(vdec)
        self.motor_RA.Target(vra)

        self.motor_DEC.Go()
        self.motor_RA.Go()
        time.sleep(0.1)

    def get_RA(self):
        p_RA = self.motor_RA.getPosition()
        return self.pos_to_RA(p_RA)

    def get_RA_speed(self):
        speed_RA = self.motor_RA.getSpeed()
        return speed_RA

    def get_DEC_speed(self):
        return 0
        speed_DEC = self.motor_DEC.getSpeed()
        return speed_DEC

    def get_DEC(self):
        p_DEC = self.motor_DEC.getPosition()
        return self.pos_to_DEC(p_DEC)
                 
    

    def track(self):
        self.RA_rate(15.041)
        self.DEC_rate(0)
        self.motor_RA.Target(10000000)
        time.sleep(0.1)

        ra0 = self.get_RA()
      

        seq = 0

        while(True):
            time.sleep(1)
            seq = seq + 1
            self.motor_RA.SpeedAdjust()
            print("v", mount.get_RA(), mount.get_DEC(), mount.get_RA_speed())
        
      
#----------------------------------------------------------

def raw_motor():
    motor = Smartmotor('COM8')
    motor.Speed(motor.calc_rps())
    motor.Acceleration(20000)
    motor.Target(1*200000)
    motor.Go()
    print(motor.getPosition())
    time.sleep(1)
    for k in range(5011):
        p0 = motor.getPosition()
        time.sleep(1)
        p1 = motor.getPosition()
        print(p1-p0, p1)
    motor.closeSerialPort()

if __name__ == '__main__':
    #raw_motor()
    mount = Mount()
    #mount.set_RA(20)

    
    mount.RA_rate(3600)
    mount.DEC_rate(1.0*3600)
    mount.target_pos(14.0, 10.5)


    while(mount.get_RA_speed()!=0 or mount.get_DEC_speed()!=0):
        print(mount.get_RA(), mount.get_DEC(), mount.get_RA_speed())
        time.sleep(0.1)


    mount.track()

    for k in range(100):
        mount.display()
        time.sleep(0.5)
        print(mount.time())




