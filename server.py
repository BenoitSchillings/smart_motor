import socket
import sys


class Server:
    def ra_to_string(self, ra):
        ra = ra * 3600

        m, s = divmod(ra, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        pattern = '%02d:%02d:%02d.%01d'
        return pattern % (h, m, s, 0)
    
    def dec_to_string(self, dec):
        sign = '+'
        if (dec < 0):
            dec = -dec
            sign = '-'
        dec = dec * 3600

        m, s = divmod(dec, 60)
        h, m = divmod(m, 60)
        d, deg = divmod(h, 60)

        pattern = '%02d*%02d:%02d'
        str =  pattern % (deg, m, s)
        return sign + str
       

    def handle_command(self, command):
        print('received "%s"' % command)
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
        
        if (command == ':RT0#'):        #Lunar tracking rate
            return '#'
        if (command == ':RT1#'):        #Solar tracking rate
            return '#'
        if (command == ':RT2#'):        #sidereal tracking rate
            return '#'
        if (command == ':RT9#'):        #Zero tracking rate
            return '#'

        if (command == ':RG0#'):        #guide rate 0.25
            return '#'
        if (command == ':RG1#'):        #guide rate 0.5
            return '#'
        if (command == ':RG2#'):        #guide rate 1.0
            return '#'

        if (command == ':RC0#'):        #center rate 12x
            return '#'
        if (command == ':RC1#'):        #center rate 64x
            return '#'
        if (command == ':RC2#'):        #center rate 600x
            return '#'
        if (command == ':RC3#'):        #center rate 1200x
            return '#'

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

        print("*******unknown ", command)
        return ''

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_address = ('localhost', 1001)
        print('starting up on %s port %s' % self.server_address)
        self.sock.bind(self.server_address)
        self.ra = 0.0
        self.dec = 0.0
        #print(self.dec_to_string(21))

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
                try:
                    #print ('connection from', client_address)
                    while True:
                        data = self.connection.recv(1024)
                        if (data):
                            result = self.handle_command(data.decode('utf-8'))
                            print(result)
                            if (result != ''):
                                print('sending data back to the client')
                                self.connection.sendall(str.encode(result))
                            else:
                                print('no more data from', self.client_address)
                                break
                finally:
                    # Clean up the connection
                    self.connection.close()



server = Server()
server.run()
