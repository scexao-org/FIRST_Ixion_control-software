################################################################################
##################		ANDOR iXon executable script		####################
################################################################################


import time
import zmq
from threading import Thread
import sys
import numpy as np
import os


import andor_science as andors
import andorCtrl_science as aCs
import andorDisplay_science as aDs


################################################################################
##################            Communication class           ####################
################################################################################


class MyException(BaseException):
    # Class made to catch errors coming from the subscriber com
    # See in class ComPortSUB
    def __init__(self, current_exception):
        self.current_exception = current_exception

    def __str__(self):
        return str(self.current_exception)


################################################################################
##################            Communication class           ####################
################################################################################


port_SUB_cmd = "tcp://localhost:5550"
andor_address = b"A"

port_PUB_print = "tcp://*:5552"
print_address = b"P"


"""

   Pubsub envelope subscriber

   Author: Guillaume Aubert (gaubert) <guillaume(dot)aubert(at)gmail(dot)com>

"""


class ComPortSUB(Thread):
    def __init__(self, publisher, port_SUB, address):
        super().__init__()
        self.running = True

        self.pub = publisher
        self.port = port_SUB
        self.address = address

        global a

        self.start()

    def _creation_socket(self):
        self.context = zmq.Context()
        self.sub = self.context.socket(zmq.SUB)
        self.sub.connect(self.port)
        self.sub.setsockopt(zmq.SUBSCRIBE, b'')
        self.pub.pprint("Com receiver is initialized (address: %s)" % (self.port))

    def run(self):
        self._creation_socket()
        while self.running:
            cmd_dict = self.sub.recv_pyobj()
            if cmd_dict["address"] == self.address:
                cmd_dict.pop("address")
                try:
                    if cmd_dict["command"] == "done()":
                        self.running = False
                        done()
                    else:
                        command = getattr(a, cmd_dict["command"])
                        cmd_dict.pop("command")
                        command(**cmd_dict)
                except Exception as cur_exception:
                    self.pub.pprint(MyException(cur_exception))
            else:
                pass

    def stop(self):
        self.pub.pprint("Com receiver is closed (address: %s)" % (self.port))
        self.sub.close()
        self.context.term()

    def start(self):
        super().start()



################################################################################
##################              Publisher class             ####################
################################################################################


class ComPortPUB(object):
    def __init__(self, port_PUB, client_address):
        self.port = port_PUB
        self.address = client_address

        self.context = zmq.Context()
        self.pub = self.context.socket(zmq.PUB)
        self.pub.bind(self.port)
        self.pprint("\n\nCom transmitter is initialized (address: %s)" % (self.port))

    def pprint(self, message):
        time.sleep(1)# need time to sleep before sending a message
        self.pub.send_multipart([self.address, str(message).encode('UTF-8')])

    def stop(self):
        self.pprint("Com transmitter is closed (address: %s)" % (self.port))
        self.pprint("done()")
        self.pub.close()
        self.context.term()


################################################################################
##################           Function definition            ####################
################################################################################


def done():
    andor_pub.pprint("Shutting down Camera....")
    a.stop()
    camera.AbortAcquisition()
    camera.SetShutter(0, 2, 300, 100)
    camera.ShutDown()
    andor_sub.stop()
    andor_pub.pprint("Camera shut down COMPLETE")
    andor_pub.stop()
    os._exit(1)


################################################################################
##################              Main process                ####################
################################################################################


if __name__ == "__main__":
    ### Initialize the communication transmitter ###
    andor_pub = ComPortPUB(port_PUB_print, print_address)


    ### Initialize the communication receiver ###
    andor_sub = ComPortSUB(andor_pub, port_SUB_cmd, andor_address)

    
    ### Initialize Andor camera ###
    cameraName = 'Ixion'
    camera = andors.Andor(cameraName)

    ## DEBUG
    '''
    Nothing much
    '''
    # Check if the good camera was initialized by checking if its serial number
    if camera.camera_serialnumber != andors.CAMERA_SERIAL[cameraName]:
        andor_pub.pprint("I'm here!")
        camera.AbortAcquisition()
        camera.ShutDown()
        del camera
        camera = andors.Andor(cameraName)


    ###	Initialise Andor Live Viewer ###
    a = aCs.AndorCtrl(camera, andor_pub)

    # Set the temperature of the detector
    cooling_temp = -20
    a.SetDetTemperature(cooling_temp)
    camera.CoolerON()
    a.GetCurrentTemperature()
    andor_pub.pprint("Detector is cooling down to %d °C..." % (cooling_temp))

    # Starts Video Feed
    a.start_cropmode()

    
    """
    ###	Initialize the plot application ###
    Qt_app = aDs.QtWidgets.QApplication(sys.argv)
    app = aDs.ApplicationWindow()
    app.set_andorCtrl(a)
    app.set_publisher(andor_pub)
    app.show()
    Qt_app.exec_()
    """
