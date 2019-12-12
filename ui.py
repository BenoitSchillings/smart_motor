import PySimpleGUI as sg
import time
from threading import Thread

gui = 0

def ui_thread(args):
        global gwindow
        
        while(True):
            time.sleep(0.1)
            gui.idle()


class UI:
    def __init__(self):
        global gui
    
        gui = self
        #print(sg.list_of_look_and_feel_values())
        sg.change_look_and_feel("Dark Red")
        layout = [
        [sg.Text('RA', pad=((11, 0), 0), font='Any 15', key='outputz1', size=(14,0)),
        sg.Text('12:32:41.2', pad=((21, 0), 0), font='Any 15', key='ra', relief = sg.RELIEF_RIDGE,size=(12,0), justification='right')],

        [sg.Text('DEC', pad=((11, 0), 0), font='Any 15', key='outputz2', size=(14,0)),
        sg.Text('+89:32:41', pad=((21, 0), 0), font='Any 15', key='dec', relief = sg.RELIEF_RIDGE, size=(12,0), justification='right')],

        [sg.VerticalSeparator(pad=(0,15))],

        [sg.Text('Rate_RA', pad=((11, 0), 0), font='Any 15', key='outputz3', size=(14,0)),
        sg.Text('+890', pad=((21, 0), 0), font='Any 15', key='rate_ra', relief = sg.RELIEF_RIDGE, size=(12,0), justification='right')],

        [sg.Text('Rate_Dec', pad=((11, 0), 0), font='Any 15', key='outputz4', size=(14,0)),
        sg.Text('+121', pad=((21, 0), 0), font='Any 15', key='rate_dec', relief = sg.RELIEF_RIDGE, size=(12,0), justification='right')],

        [sg.VerticalSeparator(pad=(0,15))],

        [sg.Text('Encoder_RA', pad=((11, 0), 0), font='Any 15', key='outputz5', size=(14,0)),
        sg.Text('1234890', pad=((21, 0), 0), font='Any 15', key='encode_ra', relief = sg.RELIEF_RIDGE, size=(12,0), justification='right')],

        [sg.Text('Encoder_Dec', pad=((11, 0), 0), font='Any 15', key='outputz6', size=(14,0)),
        sg.Text('2323321', pad=((21, 0), 0), font='Any 15', key='encode_dec', relief = sg.RELIEF_RIDGE, size=(12,0), justification='right')],

        ]

    
        self.window = sg.Window('mount', layout,
                                grab_anywhere=True,
                                keep_on_top=True,
                                #background_color='white',
                                no_titlebar=True)
        gwindow = self.window
        
                                
        thread = Thread(target=ui_thread, args=(None,))
        thread.start()
        
        
    def idle(self):
        event, values = self.window.read(timeout=0)
        #self.window['output'].update(1)
            
   

gui = UI() 

while(True):
    time.sleep(0.1)
            
            
