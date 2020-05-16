################################################################################
##################            Main control script           ####################
################################################################################
"""
This program calls the control functions for the Andor camera
written in the file "andorCtrl_science.py"

Every time a function is written for the Andor control, it should be copied here 
with the following canvas:

    def function-name(self, input-parameter):
        '''
        Function description
        '''
        command = "a.function-name(" + str(input-parameter) + ")"
        self._send(command) 

"""

import time
import os
import zmq
from threading import Thread


################################################################################
##################		                                    ####################
################################################################################


port_PUB = "tcp://*:5550"
client_address_andor = b"A"
client_address_print = b"B"

component_address = {'andor': client_address_andor, 'print': client_address_print, 'cmd': 'cmd'}


################################################################################
##################		                                    ####################
################################################################################


class AndorCmd(Thread):
    def __init__(self, publisher, address):
        self.client_address = address
        self.pub = publisher

    def _send(self, command):
        '''
        Send a command to andor process.
        '''
        self.pub.send_multipart([self.client_address, command.encode('UTF-8')])

    def set_shutter_CLOSED(self):
        '''
        Sets the internal camera shutter to CLOSED position
        '''
        command = "a.set_shutter_CLOSED()"
        self._send(command)

    def set_shutter_OPEN(self):
        '''
        Sets the internal camera shutter to OPEN position
        '''
        command = "a.set_shutter_OPEN()"
        self._send(command)

    def wait_for_idle(self, maxwaittime=10):
        command = "a.wait_for_idle(maxwaittime=" + str(maxwaittime) + ")"
        self._send(command)




    #-------------------------------------------------------------------------
    #  Start / Stop live camera
    #-------------------------------------------------------------------------

    def play(self):
        command = "a.play()"
        self._send(command)

    def pause(self):
        command = "a.pause()"
        self._send(command)

    def start(self):
        '''
        Starts the video display.
        '''
        command = "a.start()"
        self._send(command)

    def stop(self):
        command = "a.stop()"
        self._send(command)


    #-------------------------------------------------------------------------
    #  Temperature control
    #-------------------------------------------------------------------------

    def GetCurrentTemperature(self):
        command = "a.GetCurrentTemperature()"
        self._send(command)

    def SetDetTemperature(self, temperature):
        command = "a.SetDetTemperature(" + str(temperature) + ")"
        self._send(command)


    #-------------------------------------------------------------------------
    #  Acquisition Mode
    #-------------------------------------------------------------------------

    def set_single_scan(self):
        command = "a.set_single_scan()"
        self._send(command)

    def set_video_scan(self):
        command = "a.set_video_scan()"
        self._send(command)

    def get_AcquisitionTimings(self):
        command = "a.get_AcquisitionTimings()"
        self._send(command)


    #-------------------------------------------------------------------------
    #  Exposure time
    #-------------------------------------------------------------------------

    def set_exptime(self, exptime):
        '''
        Sets the camera exposure time in SECONDS.

        Example:
            a.set_exptime(0.01)

        the default exposure time at initialisation is set by a global variable:
        DEFAULT_EXP_TIME
        and is set to 0.001 - 1ms (1kHz)

        Executing this command will pause the video link while it updates then reactivate it.

        *WARNING* - Careful when subtracting darks as they will no longer match.
        '''
        command = "a.set_exptime(" + str(exptime) + ")"
        self._send(command)

    def get_exptime(self):
        command = "a.get_exptime()"
        self._send(command)


    #-------------------------------------------------------------------------
    #  Horizontal / Vertical speed
    #-------------------------------------------------------------------------

    def get_number_vs_speeds(self):
        command=  "a.get_number_vs_speeds()"
        self._send(command)

    def get_number_hs_speeds(self):
        command=  "a.get_number_hs_speeds()"
        self._send(command)

    def get_vs_speed(self):
        command = "a.get_vs_speed()"
        self._send(command)

    def get_hs_speed(self):
        command = "a.get_hs_speed()"
        self._send(command)

    def set_vs_speed(self, index):
        command = "a.set_vs_speed("+str(index)+")"
        self._send(command)

    def set_hs_speed(self, index):
        command = "a.set_hs_speed("+str(index)+")"
        self._send(command)

    def get_number_vertical_speeds(self):
        command = "a.get_number_vertical_speeds()"
        self._send(command)

    def get_number_horizontal_speeds(self):
        command = "a.get_number_horizontal_speeds()"
        self._send(command)

    def get_vertical_speed(self):
        command = "a.get_vertical_speed()"
        self._send(command)

    def get_horizontal_speed(self):
        command = "a.get_horizontal_speed()"
        self._send(command)

    def set_vertical_speed(self, index):
        command = "a.set_vertical_speed("+str(index)+")"
        self._send(command)

    def set_horizontal_speed(self, index):
        command = "a.set_horizontal_speed("+str(index)+")"
        self._send(command)





    #-------------------------------------------------------------------------
    #  Display options
    #-------------------------------------------------------------------------

    def set_clims(self, c_min, c_max):
        '''
        Function to set the colour limits of the andor video display.
        Format:
            set_clims(intiger1, intiger2) - 2>1 always otherwise will give error.

        Example:
            a.set_clims(0,10000) - locks between 0 and 10k counts

        To make auto scaling colourmap, set both variables to 'None'
            a.set_clims(None,None)


        The video display should update in realtime your changes.
        '''
        command = "a.set_clims(" + str(c_min) + "," + str(c_max) + ")"
        self._send(command)


    #-------------------------------------------------------------------------
    #  Data / Darks acquisition
    #-------------------------------------------------------------------------

    def acq_new_dark(self):
        '''
        Acquires a new dark frame for automatic subtraction on the video feed.
        The Dark is taken of whatever is on the detector at the time so make sure you turn the source off.

        Example:
            a.acq_new_dark()

        This should be re-taken whenever you change exposure time.

        It will pause the video feed while it does this and keep it internally in a variable called 'a.dark'
        '''
        command = "a.acq_new_dark()"
        self._send(command)

    def acq_cube(self, N_frames, exptime, filename=None):
        command = "a.acq_cube(" + str(N_frames) + "," + str(exptime) + ",filename='" + str(filename) + "')"
        self._send(command)


################################################################################
##################             Global functions             ####################
################################################################################


def close(component):
    '''
    Close 'component' process.
    '''
    if component == 'andor':
        publisher.send_multipart([component_address['print'], "".encode('UTF-8')])
    elif component == 'cmd':
        publisher.close()
        context.term()
        os._exit(1)
    command = "done()"
    publisher.send_multipart([component_address[component], command.encode('UTF-8')])


def done():
    '''
    Close all processes.
    '''
    for key in component_address:
        close(key)


def pprint(msg):
    command = "andor_pub.pprint(" + str(msg) + ")"
    publisher.send_multipart([client_address, command.encode('UTF-8')])


################################################################################
##################               Main process               ####################
################################################################################


"""

   Pubsub envelope publisher

   Author: Guillaume Aubert (gaubert) <guillaume(dot)aubert(at)gmail(dot)com>

"""

if __name__ == "__main__":
    ### Initialize com ###
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind(port_PUB)


    ### Initialise the andor command class ###
    a = AndorCmd(publisher, client_address_andor)


    ### Print the top messages in the terminal ###
    print("\na. controls the camera graphing and functions.")
    print("Type a.something? to view documentation about 'something'")
    print("camera. controls the camera directly through the Andor dll/SDK")
    print("Type pprint() to print. It will be printed in the other terminal.")
    print("Type done() to disconnect the camera and close viewing")
    print("Start entering commands only when the other terminal indicates camera is initialized.\n")
    