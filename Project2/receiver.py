# Written by S. Mevawala, modified by D. Gitzel
# ECE 303 Communication Networks
# Project #2
# Hongyu Wu and David Guo

import logging
import channelsimulator
import utils
import sys
import socket
import hashlib

class Receiver(object):

    def __init__(self, inbound_port=50005, outbound_port=50006, timeout=5, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)

        self.simulator.rcvr_setup(timeout)
        self.simulator.sndr_setup(timeout)

    def receive(self):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class BogoReceiver(Receiver):
    ACK_DATA = bytes(123)

    def __init__(self):
        super(BogoReceiver, self).__init__()

    def receive(self):
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        while True:
            try:
                data = self.simulator.u_receive()  # receive data
                self.logger.info("Got data from socket: {}".format(data.decode('ascii')))
                # note that ASCII will only decode bytes in the range 0-127
                sys.stdout.write(data)
                self.simulator.u_send(BogoReceiver.ACK_DATA)  # send ACK
            except socket.timeout:
                sys.exit()


def checksum(data):
    return hashlib.md5(data).hexdigest()

class RDTReceiver(Receiver):
    def __init__(self, timeout=0.1):
        super(RDTReceiver, self).__init__()
        self.simulator.sndr_socket.settimeout(timeout)
        self.simulator.rcvr_socket.settimeout(timeout)

    seqNum = 0

    def receive(self):
        lastAck = []
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        while True:
            try:
                rcvPkt = self.simulator.u_receive()  # receive data
                rcvSeqNum = rcvPkt[0:1]
                rcvCheckSum = rcvPkt[1:33]
                rcvData = rcvPkt[33:]
                chkSum = checksum(rcvData)
                if ((str(self.seqNum) == str(rcvSeqNum)) and (str(chkSum) == str(rcvCheckSum))):
                    ack = str(self.seqNum) + str(chkSum) + bytearray()
                    lastAck = ack
                    self.simulator.u_send(ack)
                    sys.stdout.write("{}".format(rcvData))
                    sys.stdout.flush()
                    # Flip bit as in alternating bit protocol
                    self.seqNum = 1 - self.seqNum
                else:
                    # Flip bit to denote nak
                    nak = str(1-self.seqNum) + str(chkSum) + bytearray()
                    self.simulator.u_send(nak) # Send NAK
      
            except socket.timeout:
                # Resend last ACK if timeout
                self.simulator.u_send(lastAck)


if __name__ == "__main__":
    # test out BogoReceiver
    rcvr = RDTReceiver()
    rcvr.receive()
