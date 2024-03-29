import socket
import sys
from parse import *


import time
import serial
import datetime
import ephem
import threading
from ui import UI

from mount import Mount

#----------------------------------------------------------

class Server:
    def ra_to_string(self, ra):
        ra = (ra / 360.0) * (24*3600)       #angle to seconds

        secfract = 10 * ((ra) % 1)
        sec = int(ra % 60)
        ra = ra - sec
        ra = ra / 60                        #in minutes

        min = int(ra % 60)

        ra = ra - min
        ra = ra / 60                        #in hours

        hours = ra

        pattern = '%02d:%02d:%02d.%01d'
        return pattern % (hours, min, sec, (secfract+0.5))
    
#------------------------------------------------------------

    def dec_to_string(self, dec):
        sign = '+'
        if (dec < 0.0):
            dec = -dec
            sign = '-'
        dec = dec * 3600

        s = dec % 60
        dec = dec / 60
        m = dec % 60
        dec = dec / 60
        deg = dec
        deg = deg % 90

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

            return ''

        if (command[0:3] == ':RG'):
            result = parse(":RG{}#", command)
            v = int(result[0])
            if (v == 0):
                print("guide 0.25")
                self.center_rate = 15*0.25
            if (v == 1):
                print("guide 0.5")
                self.center_rate = 15*0.5
            if (v == 2):
                print("guide 1.0")
                self.center_rate = 15*1.0

            return '#'

        if (command[0:3] == ':RC'):
            result = parse(":RC{}#", command)
            v = int(result[0])
            if (v == 0):
                print("center rate 12x")
                self.center_rate = 12*15
            if (v == 1):
                print("center rate 64x")
                self.center_rate = 64*15
            if (v == 2):
                print("center rate 600x")
                self.center_rate = 600*15
            if (v == 3):
                print("center rate 1200x")
                self.center_rate = 900*15
            return '#'

        if (command[0:3] == ':Sr'):             #:Sr HH:MM:SS.S# 
            result = parse(":Sr {}:{}:{}.{}#", command)
            print(result)
            self.target_ra = (int(result[0])*15.0) + (int(result[1])/4.0) + (int(result[2])/240.0)
      
            #print(result)
            return '1'
        if (command[0:3] == ':Sd'):
            result = parse(":Sd {}*{}:{}#", command)   #:Sd sDD*MM:SS# 
            r0 = int(result[0])
            sign = 1
            if (result[0][0] == '-'):
                r0 = - r0
                sign = -1
            self.target_dec = sign*((r0 + int(result[1])/60.0) + (int(result[2])/(3600.0)))

            #print(result)
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
        #print('received "%s"' % command)
        if (self.is_complex(command)):
            return self.handle_complex(command)



        if (command == '#'):
            return '#'
        if (command == ':V#'):
            return '1.0#'
        if (command == ':U#'):
            return '#'

        if (command == ':GR#'):         #RA
            str = self.ra_to_string(mount.last_ra)
            self.gui.set('RA', str)
            return str + "#"

        if (command == ':GD#'):         #DEC
            str = self.dec_to_string(mount.last_dec)
            self.gui.set('DEC', str)
            return str + '#'


        if (command == ':GS#'):         
            return '01:23:45.6#'        #SIDEREAL TIME

        if (command == ':pS#'):         #side of mount
            return 'East#'
        if (command == ':Mn#'):         #move north
            mount.req_tracking_rate_dec = (self.center_rate)
            return '#'
        if (command == ':Ms#'):         #move south
            mount.req_tracking_rate_dec = (-self.center_rate)
            return '#'
        if (command == ':Me#'):         #move east
            mount.req_tracking_rate_ra = 15.041 + -self.center_rate
            return '#'
        if (command == ':Mw#'):         #move west
            mount.req_tracking_rate_ra = 15.041 + self.center_rate
            return '#'

        if (command == ':Q#'):          #stop motion
            mount.req_tracking_rate_ra = 15.041
            mount.req_tracking_rate_dec = 0

            mount.interrupt = True
            return '#'

        if (command == ':MS#'):         #slew to target
            mount.goto_ra = self.target_ra
            mount.goto_dec = self.target_dec
            mount.goto = True

            return '0'

        if (command == ':CM#'):
            mount.sync_ra = self.target_ra
            mount.sync_dec = self.target_dec
            mount.sync = True
            return 'Coordinates     matched.        #'

        if (command == ':CMR#'):
            mount.sync_ra = self.target_ra
            mount.sync_dec = self.target_dec
            mount.sync = True
            return 'Coordinates     matched.        #'

        print("*******unknown ", command)
        return '#'

#------------------------------------------------------------


    def __init__(self, gui):
        self.gui = gui
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_address = ('localhost', 1001)
        print('starting up on %s port %s' % self.server_address)
        self.sock.bind(self.server_address)
        self.ra = 0.0
        self.dec = 0.0
        self.target_ra = 0.0
        self.target_dec = 0.0
        
        self.center_rate = 64*15



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
                            #self.gui.set("Last",(data.decode('utf-8') + result))
                            if (result != ''):
                                self.connection.sendall(str.encode(result))
                            else:
                                print('no more data from', self.client_address)
                                break
                except:
                    print("timeout", sys.exc_info())  
                finally:
                    # Clean up the connection
                    self.connection.close()


#------------------------------------------------------------

mount = 0
NOPOS = -9999

def handle_goto(mount):
    mount.motor_RA.Position()
    mount.motor_DEC.Position()
    print("t0", time.clock())

    mount.interrupt = False
    
    mount.RA_rate(3*3600)
    mount.DEC_rate(3*3600)
    print("start goto ", mount.goto_ra, mount.goto_dec)
    mount.target_pos(mount.goto_ra, mount.goto_dec)
    mount.goto = False

    while((mount.get_RA_speed() != 0 or
          mount.get_DEC_speed() != 0) and
          mount.interrupt == False):
        gui.set("Rate_RA", mount.get_RA_speed())
        gui.set("Rate_DEC", mount.get_DEC_speed())
        #print("going goto", mount.get_RA(), mount.get_DEC(), mount.get_RA_speed(), mount.get_DEC_speed())
        time.sleep(0.05)


    if (mount.interrupt == True):
        print("interupt")
    else:
        mount.target_pos(mount.goto_ra, mount.goto_dec)

    mount.goto_ra = NOPOS
    mount.goto_dec = NOPOS


    print("t1", time.clock())
    mount.RA_rate(mount.tracking_rate_ra)
    mount.tracking_rate_dec = 0

#----------------------------------------------------------
        
def handle_sync(mount):
    mount.set_RA(mount.sync_ra)
    mount.set_DEC(mount.sync_dec)
    mount.sync_ra = NOPOS
    mount.sync_dec = NOPOS
    mount.sync = False

#----------------------------------------------------------

def motor_thread(gui):
    global mount


    #print("gui is ", gui)
    mount = Mount(gui)
    print("max = ", mount.ra_to_pos(359.999))
    mount.interrupt = False

    mount.req_tracking_rate_ra = 15.041
    mount.req_tracking_rate_dec = 0

    mount.tracking_rate_ra = 0.0
    mount.tracking_rate_dec = 0.0

    mount.goto_ra = NOPOS
    mount.goto_dec = NOPOS
    mount.goto = False
    mount.sync = False
    phase = 0

    while(True):
        time.sleep(0.02)
        phase = phase + 1
        if (mount.req_tracking_rate_ra != mount.tracking_rate_ra or
            mount.req_tracking_rate_dec != mount.tracking_rate_dec):
    
            mount.tracking_rate_ra = mount.req_tracking_rate_ra
            mount.tracking_rate_dec = mount.req_tracking_rate_dec

            mount.RA_rate(mount.tracking_rate_ra)
            mount.DEC_rate( mount.tracking_rate_dec)
            mount.motor_RA.Velocity()
            mount.motor_DEC.Velocity()
            


        if (mount.goto == True):
            print("GOTO")
            handle_goto(mount)
            mount.RA_rate(mount.tracking_rate_ra)
            mount.DEC_rate(mount.tracking_rate_dec)
            mount.motor_RA.Velocity()
            mount.motor_DEC.Velocity()
            
        if (mount.sync == True):
            handle_sync(mount)
            mount.motor_RA.Velocity()
            mount.motor_DEC.Velocity()
        
        ra = mount.get_RA()
        dec = mount.get_DEC()

        if (phase % 30 == 0):
            mount.motor_RA.SpeedAdjust()
            mount.motor_DEC.SpeedAdjust()

        if (phase % 15 == 0):
            gui.set("Rate_RA", mount.get_RA_speed())
            gui.set("Rate_DEC", mount.get_DEC_speed())


#----------------------------------------------------------


gui = UI()

x = threading.Thread(target=motor_thread, args=(gui,), daemon=True)
x.start()

server = Server(gui)

server.run()
