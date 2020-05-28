################################################################################
##################           Show output messages           ####################
################################################################################


import os
import time
import zmq
from threading import Thread


################################################################################
##################              Global variables            ####################
################################################################################


port_SUB_Cmd = "tcp://localhost:5551"
port_SUB_andor = "tcp://localhost:5552"

component_port = {'andor': port_SUB_andor,
                  'cmd': port_SUB_Cmd}

server_address = b"P"


################################################################################
##################           Communication process          ####################
################################################################################


#   Reading from multiple sockets
#   This version uses zmq.Poller()
#
#   Author: Jeremy Avnet (brainsik) <spork(dash)zmq(at)theory(dot)org>
#


class ComPortSUB(Thread):
    def __init__(self, port_dict, address):
        super().__init__()
        self.running = True

        self.port = port_dict
        self.address = address

        self.connected_pub = ['cmd']
        self.subscriber_context = dict()

        # Prepare our context and sockets
        self.context = zmq.Context()
        self._creation_socket()

        # Start the Thread
        super().start()

        print("##########")
        print("Ready to print messages...")
        print("##########")

    def _creation_socket(self):
        # Connect to all servers
        for comp, port in self.port.items():
            self.subscriber_context[comp] = self.context.socket(zmq.SUB)
            self.subscriber_context[comp].connect(port)
            self.subscriber_context[comp].setsockopt(zmq.SUBSCRIBE, self.address)

        # Initialize poll set
        self.poller = zmq.Poller()
        for comp in self.subscriber_context:
            self.poller.register(self.subscriber_context[comp], zmq.POLLIN)

    def run(self):
        """
        Process messages from all the sockets.
        """
        while True:
            try:
                socks = dict(self.poller.poll())
            except KeyboardInterrupt:
                break

            for component, subscriber in self.subscriber_context.items():
                if subscriber in socks:
                    if component not in self.connected_pub:
                        self.connected_pub.append(component)

                    address, contents = subscriber.recv_multipart()

                    contents_UTF = contents.decode('UTF-8')
                    if contents_UTF == "done()":
                        self.connected_pub.pop(self.connected_pub.index(component))
                        self.running = False
                    elif contents_UTF == "forcequit":
                        # Empty the list to exit the while loop
                        self.connected_pub = []
                        self.running = False
                    else:
                        print(contents_UTF)
                else:
                    pass
                time.sleep(0.1)

            # Exit loop
            if (not self.running) and (len(self.connected_pub) == 0):
                break

        # To stop the Thread and close the object
        self.stop()
    
    def stop(self):
        """
        Close all the sockets and the context.
        """
        for comp in self.subscriber_context:
            self.subscriber_context[comp].close()
        self.context.term()

        # Close the main process
        done()


################################################################################
##################             Global functions             ####################
################################################################################


def done():
    print("Terminal is closing in 2 sec...")
    time.sleep(2)
    os._exit(1)


################################################################################
##################              Main process                ####################
################################################################################


if __name__ == "__main__":
    ### Initialize the communication receiver ###
    print_sub = ComPortSUB(component_port, server_address)
