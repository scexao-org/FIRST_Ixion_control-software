################################################################################
##################            Main control script           ####################
################################################################################
"""
This program calls the control functions for the Andor camera
written in the file "andorCtrl_science.py".

It allows the user to type commands with their names in order to execute
them and send a corresponding command to the script "andorCtrl_science.py"
in which it will be executed.

"""

import time
import os
import zmq
from threading import Thread
from andorCtrl_science import AndorCtrl


################################################################################
##################             Global variables             ####################
################################################################################


# Communication
port_PUB_comps = "tcp://*:5550"
port_PUB_print = "tcp://*:5551"

client_address_print = b"P"
client_address_andor = b"A"

component_address = {'print': client_address_print, 
                     'andor': client_address_andor, 
                     'cmd': 'cmd'}


################################################################################
##################           Decorators definition          ####################
################################################################################


def add_command(comp_method):
    def decorator(original_method):
        def modified_func(*args, **kwargs):
            kwargs['command'] = comp_method
            return original_method(*args, **kwargs)

        return modified_func

    return decorator


def cmd_compatibility():
    def decorator(cmd_method):
        """The decorator."""

        def modified_func(self, *args, **kwargs):
            """Check if the given arguments (args and kwargs) correspond
            to those needed to comp_method."""

            # Retrieve the component method
            comp_method = kwargs['command']

            # Retrieve the args and the kwargs of the component method
            comp_arguments = comp_method.__code__.co_varnames
            len_arguments = comp_method.__code__.co_argcount
            comp_kwargs_value = comp_method.__defaults__

            # Check if the given kwargs (kwargs) are the same as the expected ones (comp_arguments)
            if comp_kwargs_value is not None:
                len_diff = len_arguments - len(comp_kwargs_value)  # Nbre of unamed arguments

                for key in kwargs:
                    if (key != 'command') and (key not in comp_arguments[len_diff:]):
                        raise TypeError("{0}() got an unexpected keyword argument '{1}'"
                            .format(comp_method.__name__, key))
            else:
                len_diff = len_arguments
            
            if len_diff > 1:
                # Check if there is the right number of expected arguments given
                if len_diff - 1 != len(args):
                    raise TypeError("{0}() takes {1} positional argument but {2} were given"
                                    .format(comp_method.__name__, len_diff - 1, len(args)))

                # Put the unamed arguments in kwargs
                for i in range(1, len_diff):
                    kwargs[comp_arguments[i]] = args[i-1]

            return cmd_method(self, *args, **kwargs)

        return modified_func

    return decorator


################################################################################
##################              Command class               ####################
################################################################################


class FirstCommand:
    def __init__(self, comp_class, publisher, address):
        self.comp_class = comp_class
        self.pub = publisher
        self.client_address = address

        # Retrieve the methods of the component class
        comp_class_dict = self.comp_class.__dict__

        # Set all the methods according to the component class
        for key, value in comp_class_dict.items():
            if not key.startswith('__'):
                self.__dict__[key] = add_command(value)(self.send_pyobj_cmd)

    @cmd_compatibility()
    def send_pyobj_cmd(self, *args, **kwargs):
        """
        Customised send_pyobj() function, embedding the address and sending parameters.
        Look at the scripts named as "*ctrl.py" to have help for functions.
        """
        kwargs['command'] = kwargs['command'].__name__
        kwargs["address"] = self.client_address
        for key, value in kwargs.items():
            print(key, value)
        self.pub.send_pyobj(kwargs)


################################################################################
##################		                                    ####################
################################################################################

"""
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
"""

################################################################################
##################             Global functions             ####################
################################################################################


def close(component, **kwargs):
    command = "done()"
    if component == 'print':
        pub_print.send_multipart([component_address[component], command.encode('UTF-8')])
    elif component == 'cmd':
        publisher_comps.close()
        pub_print.close()
        context.term()
        os._exit(1)
    else:
        kwargs["address"] = component_address[component]
        kwargs["command"] = command
        publisher_comps.send_pyobj(kwargs)


def done():
    for key in component_address:
        if key != 'cmd':
            close(key)
    else:
        close('cmd')

"""
def close(component):
    '''
    Close 'component' process.
    '''
    if component == 'andor':
        publisher_comps.send_multipart([component_address['print'], "".encode('UTF-8')])
    elif component == 'cmd':
        publisher_comps.close()
        context.term()
        os._exit(1)
    command = "done()"
    publisher_comps.send_multipart([component_address[component], command.encode('UTF-8')])


def done():
    '''
    Close all processes.
    '''
    for key in component_address:
        close(key)


def pprint(msg):
    command = "andor_pub.pprint(" + str(msg) + ")"
    publisher_comps.send_multipart([client_address, command.encode('UTF-8')])
"""

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
    publisher_comps = context.socket(zmq.PUB)
    publisher_comps.bind(port_PUB_comps)


    ### Initialise the andor command class ###
    # a = AndorCmd(publisher_comps, client_address_andor)
    a = FirstCommand(AndorCtrl, publisher_comps, client_address_andor)


    ### Print the top messages in the terminal ###
    print("\na. controls the camera graphing and functions.")
    print("Type a.something? to view documentation about 'something'")
    print("camera. controls the camera directly through the Andor dll/SDK")
    print("Type pprint() to print. It will be printed in the other terminal.")
    print("Type done() to disconnect the camera and close viewing")
    print("Start entering commands only when the other terminal indicates camera is initialized.\n")


    ### Initialise com with the print terminal ###
    pub_print = context.socket(zmq.PUB)
    pub_print.bind(port_PUB_print)

    time.sleep(0.1)
    pub_print.send_multipart([client_address_print, "".encode('UTF-8')])
