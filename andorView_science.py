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


port_SUB = "tcp://localhost:5550"
port_PUB = "tcp://*:5551"
client_adress = b"B"


"""

   Pubsub envelope subscriber

   Author: Guillaume Aubert (gaubert) <guillaume(dot)aubert(at)gmail(dot)com>

"""

class ComPortSUB(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.running = False
        global andor_pub

    def _creation_socket(self):
        self.context = zmq.Context()
        self.sub = self.context.socket(zmq.SUB)
        self.sub.connect(port_SUB)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"A")
        andor_pub.pprint("Com receiver is initialized")

    def run(self):
        self._creation_socket()
        self.running = True
        while self.running:
            [address, command] = self.sub.recv_multipart()
            try:
                exec(command)
            except Exception as cur_exception:
                andor_pub.pprint(MyException(cur_exception))

    def stop(self):
        andor_pub.pprint("Com receiver is closed")
        self.running = False
        self.sub.close()
        self.context.term()



class ComPortPUB(object):
    def __init__(self):
        self.context = zmq.Context()
        self.pub = self.context.socket(zmq.PUB)
        self.pub.bind("tcp://*:5551")
        self.pprint("\nCom transmitter is initialized")

    def pprint(self, message):
        time.sleep(1)# need time to sleep before sending a message
        self.pub.send_multipart([client_adress, str(message).encode('UTF-8')])

    def stop(self):
        self.pprint("Com transmitter is closed")
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
    camera.SetShutter(0,2,300,100)
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
    andor_pub = ComPortPUB()


    ### Initialize the communication receiver ###
    andor_sub = ComPortSUB()
    andor_sub.start()

    
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

    
    # ###	Initialize the plot application ###
    # Qt_app = aDs.QtWidgets.QApplication(sys.argv)
    # app = aDs.ApplicationWindow()
    # app.set_andorCtrl(a)
    # app.set_publisher(andor_pub)
    # app.show()
    # Qt_app.exec_()