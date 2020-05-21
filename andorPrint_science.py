################################################################################
##################           Show output messages           ####################
################################################################################


import os
import time
import zmq


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

        self.connected_pub = list()
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
                    elif contents_UTF == "close()":
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


"""
if __name__ == "__main__":
    #   Reading from multiple sockets
    #   This version uses zmq.Poller()
    #
    #   Author: Jeremy Avnet (brainsik) <spork(dash)zmq(at)theory(dot)org>
    #

    # Prepare our context and sockets
    context = zmq.Context()

    # Connect to Cmd server
    subscriber_Cmd = context.socket(zmq.SUB)
    subscriber_Cmd.connect(port_SUB_Cmd)
    subscriber_Cmd.setsockopt(zmq.SUBSCRIBE, server_address)
    subscriber_context['Cmd'] = subscriber_Cmd

    # Connect to andor server
    subscriber_andor = context.socket(zmq.SUB)
    subscriber_andor.connect(port_SUB_andor)
    subscriber_andor.setsockopt(zmq.SUBSCRIBE, server_address)
    subscriber_context['Andor'] = subscriber_andor

    # Initialize poll set
    poller = zmq.Poller()
    poller.register(subscriber_Cmd, zmq.POLLIN)
    poller.register(subscriber_andor, zmq.POLLIN)

    print("##########")
    print("Ready to print messages...")
    print("##########")

    # Process messages from both sockets
    stop = False
    while True:
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        for component, subscriber in subscriber_context.items():
            if subscriber in socks:
                if component not in connected_pub:
                    connected_pub.append(component)

                address, contents = subscriber.recv_multipart()

                contents_UTF = contents.decode('UTF-8')
                if contents_UTF == "done()":
                    connected_pub.pop(connected_pub.index(component))
                    stop = True
                else:
                    print(contents_UTF)
            else:
                pass
            time.sleep(0.1)

        # Exit loop
        if stop and len(connected_pub) == 0:
            break


    # To finish the process and exit
    subscriber_Cmd.close()
    subscriber_andor.close()
    context.term()
    print("Process is closing in 2 sec...")
    time.sleep(2)
    os._exit(1)
"""

if __name__ == "__main__":
    ### Initialize the communication receiver ###
    print_sub = ComPortSUB(component_port, server_address)
