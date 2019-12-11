import socket
import sys
from parse import *


import time
import serial
import datetime
import ephem
import threading

#----------------------------------------------------------

class Mount:
    def __init__(self):
        self.motor_DEC = Smartmotor('COM8')
        self.motor_RA = Smartmotor('COM9')
        self.motor_DEC.Acceleration(120)
        self.motor_RA.Acceleration(120)
        self.ephem = ephem.city('San Francisco')
        self.sky_angle = self.siderial_angle()

    def set_RA(self, ra):
        self.motor_RA.SetPos(self.ra_to_pos(ra))


    def set_DEC(self, dec):
        self.motor_DEC.SetPos(self.dec_to_pos(dec))


    def siderial_angle(self):
        self.ephem.date = datetime.datetime.now()
        return 57.29580026*self.ephem.sidereal_time()


    def RA_Rotation(self):                              #angle per worm gear rotation
        return(360.0/225.0)

    def DEC_Rotation(self):                             #angle per worm gear rotation
        return(360.0/225.0)

    def RA_rate(self, rate=15.0):                       #motion rate (in arcsec per second)
        unity_rate_0 = self.motor_RA.calc_rps()
        unity_rate = self.RA_Rotation() * 3600.0        #this would be one RPS arcsec rate
        divider = rate / unity_rate
        self.motor_RA.Speed(unity_rate_0 * divider)
        self.motor_RA.Go()

    def DEC_rate(self, rate=0.0):                       #motion rate (in arcsec per second)
        unity_rate_0 = self.motor_DEC.calc_rps()
        unity_rate = self.DEC_Rotation() * 3600.0       #this would be one RPS arcsec rate
        divider = rate / unity_rate
        self.motor_DEC.Speed(unity_rate_0 * divider)
        self.motor_DEC.Go()


    def ra_to_pos(self, ra):                            #map RA value (0..360) to target encoder value
        delta_RA = self.siderial_angle()                #second for the reference RA
        ra = ra + delta_RA
        ra = ra % 360

        ra = ra / self.RA_Rotation()
        ra = self.motor_RA.rotation_to_position(ra)
        
        return ra      

    def dec_to_pos(self, dec):                          #map DEC value (-90..90) to target encoder value
        dec = dec / self.DEC_Rotation()
        dec = self.motor_DEC.rotation_to_position(dec)
        return dec


    def pos_to_RA(self, pos):                           # map encoder to RA
        pos = self.motor_RA.position_to_rotation(pos)
        pos = pos * self.RA_Rotation()
        delta_RA = self.siderial_angle()
        ra = pos - delta_RA
        ra = ra % 360

        return ra       

    def pos_to_DEC(self, pos):                          #map encoder to DEC
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
        if (ra > 360.0 or ra < 0.0):
            ra = ra % 360
            self.set_RA(ra)

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
    
    mount.RA_rate(4*3600)
    mount.DEC_rate(4*3600)
    print("start goto ", mount.goto_ra, mount.goto_dec)
    mount.target_pos(mount.goto_ra, mount.goto_dec)
    mount.goto_ra = NOPOS
    mount.goto_dec = NOPOS
    mount.goto = False

    while((mount.get_RA_speed() != 0 or
          mount.get_DEC_speed() != 0) and
          mount.interrupt == False):
        print("going goto", mount.get_RA(), mount.get_DEC(), mount.get_RA_speed(), mount.get_DEC_speed())
        time.sleep(0.1)


    if (mount.interrupt == True):
        print("interupt")
    mount.tracking_rate_ra = 0
    mount.tracking_rate_dec = 0

#----------------------------------------------------------
        
def handle_sync(mount):
    mount.set_RA(mount.sync_ra)
    mount.set_DEC(mount.sync_dec)
    mount.sync_ra = NOPOS
    mount.sync_dec = NOPOS
    mount.sync = False

#----------------------------------------------------------

def motor_thread(name):
    global mount

    mount = Mount()
    
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
            mount.DEC_rate( mount.tracking_rate_dec)
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
            print("v", ra, dec, mount.get_RA_speed(), mount.get_DEC_speed())



