################################################################################
#######################		ANDOR iXon TEST  script		########################
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


port_SUB = "tcp://localhost:5550"
port_PUB = "tcp://*:5551"
client_adress = b"B"

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


### Initialize the communication transmitter ###
andor_pub = ComPortPUB()


### Initialize the communication receiver ###
andor_sub = ComPortSUB()
andor_sub.start()

### Initialize Andor camera ###
cameraName = 'Ixion'
camera = andors.Andor(cameraName)


###	Initialise Andor Live Viewer ###
a = aCs.AndorCtrl(camera, andor_pub)