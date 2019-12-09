import socket
import sys
from parse import *


import time
import serial
import datetime
import ephem
import threading

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
        ra = self.pos_to_RA(p_RA)
        self.last_ra = ra
        return ra

    def get_RA_speed(self):
        speed_RA = self.motor_RA.getSpeed()
        return speed_RA

    def get_DEC_speed(self):
        speed_DEC = self.motor_DEC.getSpeed()
        return speed_DEC

    def get_DEC(self):
        p_DEC = self.motor_DEC.getPosition()
        dec = self.pos_to_DEC(p_DEC)
        self.last_dec = dec
        return dec
                 
    

    def track(self, rate_ra, rate_dec):
        self.RA_rate(rate_ra)
        self.DEC_rate(rate_dec)

        self.motor_RA.writeser('MV ')
        self.motor_DEC.writeser('MV ')
        self.motor_DEC.Go()
        self.motor_RA.Go()

        seq = 0

        while(True):
            time.sleep(1)
            seq = seq + 1
            self.motor_RA.SpeedAdjust()
            self.motor_DEC.SpeedAdjust()
            print("v", self.get_RA(), self.get_DEC(), self.get_RA_speed(), self.get_DEC_speed())
        
      
#----------------------------------------------------------

mount = 0
NOPOS = -9999

def handle_goto(mount):
    mount.motor_RA.Position()
    mount.motor_DEC.Position()
    mount.interrupt = False

    mount.RA_rate(3600)
    mount.DEC_rate(1.0*3600)
    mount.target_pos(mount.goto_ra, mount.goto_dec)
    mount.goto_ra = NOPOS
    mount.goto_dec = NOPOS

    while((mount.get_RA_speed() != 0 or
          mount.get_DEC_speed() != 0) and
          mount.interrupt == False):
        print("goto", mount.get_RA(), mount.get_DEC(), mount.get_RA_speed(), mount.get_DEC_speed())
        time.sleep(0.1)


    if (mount.interrupt == True):
        print("interupt")
    mount.tracking_rate_ra = 0
    mount.tracking_rate_dec = 0
        
def handle_sync(mount):
    mount.set_RA(mount.sync_ra)
    mount.set_DEC(mount.sync_dec)
    mount.sync_ra = NOPOS
    mount.sync_dec = NOPOS
    mount.sync = False


def motor_thread(name):
    global mount

    mount = Mount()
    
    mount.interrupt = False

    mount.req_tracking_rate_ra = 15.041
    mount.req_tracking_rate_dec = 20.0

    mount.tracking_rate_ra = 0.0
    mount.tracking_rate_dec = 0.0

    mount.goto_ra = NOPOS
    mount.goto_dec = NOPOS
    mount.goto = False
    phase = 0

    while(True):
        time.sleep(0.03)
        phase = phase + 1
        if (mount.req_tracking_rate_ra != mount.tracking_rate_ra or
            mount.req_tracking_rate_dec != mount.tracking_rate_dec):
    
            mount.tracking_rate_ra = mount.req_tracking_rate_ra
            mount.tracking_rate_dec = mount.req_tracking_rate_dec

            mount.RA_rate(mount.tracking_rate_ra)
            mount.DEC_rate( mount.tracking_rate_dec)
            mount.motor_RA.Velocity()
            mount.motor_DEC.Velocity()
            print("set rate")


        if (mount.goto == True):
            handle_goto(mount)
            
        if (mount.sync == True):
            handle_sync(mount)
        
        ra = mount.get_RA()
        dec = mount.get_DEC()

        if (phase % 30 == 0):
            mount.motor_RA.SpeedAdjust()
            mount.motor_DEC.SpeedAdjust()
            print("v", ra, dec, mount.get_RA_speed(), mount.get_DEC_speed())



#------------------------------------------------------------

class Server:
    def ra_to_string(self, ra):
        ra = (ra / 360.0) * (24*3600)       #angle to seconds

        sec = int(ra % 60)
        ra = ra - sec
        ra = ra / 60                        #in minutes

        min = int(ra % 60)

        ra = ra - min
        ra = ra / 60                        #in hours

        hours = ra

        pattern = '%02d:%02d:%02d.%01d'
        return pattern % (hours, min, sec, 0)
    
#------------------------------------------------------------

    def dec_to_string(self, dec):
        sign = '+'
        if (dec < 0):
            dec = -dec
            sign = '-'
        dec = dec * 3600

        s = dec % 60
        dec = dec / 60
        m = dec % 60
        dec = dec / 60
        deg = dec

        pattern = '%02d*%02d:%02d'
        str =  pattern % (deg, m, s)
        return sign + str
       
#------------------------------------------------------------

#check for numerical value before the # at the end of the command
#this will define a command which has to be parsed


    def is_complex(self, command):
        if (len(command) == 1):
            return False

        char = command[-2]

        if (char >= '0' and char <= '9'):
            return True
        return False
        
#------------------------------------------------------------

    def handle_complex(self, command):
        if (command[0:3] == ':RT'):
            result = parse(":RT{}#", command)
            v = int(result[0])
            if (v == 0):
                print("lunar speed")
            if (v == 1):
                print("Solar speed")
            if (v == 2):
                print("sidereal speed")
            if (v == 9):
                print("zero speed")

            return '#'

        if (command[0:3] == ':RG'):
            result = parse(":RG{}#", command)
            v = int(result[0])
            if (v == 0):
                print("guide 0.25")
            if (v == 1):
                print("guide 0.5")
            if (v == 2):
                print("guide 1.0")

            return '#'

        if (command[0:3] == ':RC'):
            result = parse(":RC{}#", command)
            v = int(result[0])
            if (v == 0):
                print("center rate 12x")
            if (v == 1):
                print("center rate 64x")
            if (v == 2):
                print("center rate 600x")
            if (v == 2):
                print("center rate 1200x")
            return '#'

        if (command[0:3] == ':Sr'):             #:Sr HH:MM:SS.S# 
            result = parse(":Sr {}:{}:{}.{}#", command)
            self.target_ra = (int(result[0])*15.0) + (int(result[1])/4.0) + (int(result[2])/240.0)
      
            print(result)
            return '1'
        if (command[0:3] == ':Sd'):
            result = parse(":Sd {}*{}:{}#", command)   #:Sd sDD*MM:SS# 
            r0 = int(result[0])
            sign = 1
            if (r0 < 0.0):
                r0 = - r0
                sign = -1
            self.target_dec = sign*((r0 + int(result[1])/60.0) + (int(result[2])/(3600.0)))

            print(result)
            return '1'


        if (command[0:3] == ':RR'): #:RR sxxx.xxxx# Selects the tracking rate in the RA axis to xxx.xxxx
            result = parse(":RR {}#", command)
            print("rate RA is ", result[0])
            return('1')

        if (command[0:3] == ':RD'): #:RD sxxx.xxxx# Selects the tracking rate in the DEC axis to xxx.xxxx
            result = parse(":RD {}#", command)
            print("rate DEC is ", result[0])
            return('1')



    
#------------------------------------------------------------

    def handle_command(self, command):
        print('received "%s"' % command)
        if (self.is_complex(command)):
            return self.handle_complex(command)



        if (command == '#'):
            return '#'
        if (command == ':V#'):
            return '1.0#'
        if (command == ':U#'):
            return '#'

        if (command == ':GR#'):         #RA
            return self.ra_to_string(mount.last_ra) + "#"

        if (command == ':GD#'):         #DEC
            return self.dec_to_string(mount.last_dec) + '#'


        if (command == ':GS#'):         
            return '01:23:45.6#'        #SIDEREAL TIME

        if (command == ':pS#'):         #side of mount
            return 'East#'

        if (command == ':Mn#'):         #move north
            self.dec -= 0.1
            return '#'
        if (command == ':Ms#'):         #move south
            self.dec += 0.1
            return '#'
        if (command == ':Me#'):         #move east
            self.ra += 0.1
            return '#'
        if (command == ':Mw#'):         #move west
            self.ra -= 0.1
            return '#'

        if (command == ':Q#'):          #stop motion
            mount.interrupt = True
            return '#'

        if (command == ':MS#'):         #slew to target
            self.ra = self.target_ra
            self.dec = self.target_dec

            return '0'

        if (command == ':CM#'):
            self.ra = self.target_ra
            self.dec = self.target_dec
            mount.goto_ra = self.ra
            mount.goto_dec = self.dec
            mount.goto = True
            return 'Coordinates     matched.        #'

        if (command == ':CMR#'):
            self.ra = self.target_ra
            self.dec = self.target_dec
            mount.sync_ra = self.ra
            mount.sync_dec = self.dec
            mount.sync = True
           return 'Coordinates     matched.        #'

        print("*******unknown ", command)
        return '#'

#------------------------------------------------------------


    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_address = ('localhost', 1001)
        print('starting up on %s port %s' % self.server_address)
        self.sock.bind(self.server_address)
        self.ra = 0.0
        self.dec = 0.0
        self.target_ra = 0.0
        self.target_dec = 0.0

        #print(self.ra_to_string(30.2))
        #print(self.dec_to_string(70.5))

    def run(self):
        self.sock.listen(1)
        self.sock.settimeout(1.0)
 
        while True:
            try:
                self.connection, self.client_address = self.sock.accept()
                valid = True
            except:
                valid = False

           
            if (valid):
                self.connection.settimeout(3.0)
                try:
                    while True:
                        data = self.connection.recv(1024)
                        if (data):
                            result = self.handle_command(data.decode('utf-8'))
                            print(result)
                            if (result != ''):
                                self.connection.sendall(str.encode(result))
                            else:
                                print('no more data from', self.client_address)
                                break
                except:
                    print("timeout")  
                finally:
                    # Clean up the connection
                    self.connection.close()


#------------------------------------------------------------

x = threading.Thread(target=motor_thread, args=(1,), daemon=True)
x.start()

server = Server()
server.run()
