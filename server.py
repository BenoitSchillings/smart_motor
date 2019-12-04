import socket
import sys
from parse import *

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
        print("complex ", command)
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
            return self.ra_to_string(self.ra) + "#"

        if (command == ':GD#'):         #DEC
            return self.dec_to_string(self.dec) + '#'


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
            return '#'

        if (command == ':MS#'):         #slew to target
            self.ra = self.target_ra
            self.dec = self.target_dec

            return '0'

        if (command == ':CM#'):
            self.ra = self.target_ra
            self.dec = self.target_dec
            return 'Coordinates     matched.        #'

        if (command == ':CMR#'):
            self.ra = self.target_ra
            self.dec = self.target_dec
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
                    #print ('connection from', client_address)
                    while True:
                        data = self.connection.recv(1024)
                        print("wait")
                        if (data):
                            result = self.handle_command(data.decode('utf-8'))
                            print(result)
                            if (result != ''):
                                print('sending data back to the client')
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



server = Server()
server.run()
