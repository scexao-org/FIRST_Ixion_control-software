################################################################################
##################           Show output messages           ####################
################################################################################


import os
import time
import zmq


################################################################################
##################             Global definition            ####################
################################################################################


port_SUB_Cmd = "tcp://localhost:5550"
port_SUB_andor = "tcp://localhost:5551"
server_address = b"B"

connected_pub = list()
subscriber_context = dict()


################################################################################
##################           Communication process          ####################
################################################################################


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
    port_SUB = "tcp://localhost:5551"
    server_adress = b"B"
    # Prepare our context
    context = zmq.Context()

    # Socket to receive messages on
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(port_SUB)
    subscriber.setsockopt(zmq.SUBSCRIBE, server_adress)
    print("##########")
    print("Ready to print messages...")
    print("##########")

    while True:
        # Read envelope with address
        [address, contents] = subscriber.recv_multipart()
        contents_UTF = contents.decode('UTF-8')

        if contents_UTF == "done()":
            break
        else:
            print(contents_UTF)

    # To finish the process and exit
    subscriber.close()
    context.term()
    """