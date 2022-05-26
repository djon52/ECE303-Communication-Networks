# Written by S. Mevawala, modified by D. Gitzel
# ECE 303 Communication Networks
# Project #2
# Hongyu Wu and David Guo

import logging
import socket
import channelsimulator
import utils
import sys
import hashlib

class Sender(object):

    def __init__(self, inbound_port=50006, outbound_port=50005, timeout=1, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.sndr_setup(timeout)
        self.simulator.rcvr_setup(timeout)

    def send(self, data):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class BogoSender(Sender):

    def __init__(self):
        super(BogoSender, self).__init__()

    def send(self, data):
        self.logger.info(
            "Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))
        while True:
            try:
                self.simulator.u_send(data)  # send data
                ack = self.simulator.u_receive()  # receive ACK
                self.logger.info("Got ACK from socket: {}".format(
                    ack.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
                break
            except socket.timeout:
                pass


def checksum(data):
    return hashlib.md5(data).hexdigest()

class RDTSender(Sender):

    def __init__(self, timeout=0.1, pktSize=950, maxSeqNum=256):
        super(RDTSender, self).__init__()
        self.pktSize = pktSize
        self.maxSeqNum = maxSeqNum
        self.simulator.sndr_socket.settimeout(timeout)
        self.simulator.rcvr_socket.settimeout(timeout)

    seqNum = 0
    pktStart = 0
    sndPkt = []

    def send(self, data):
        self.logger.info("Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))
        res = False # bool to determine if to resend or send next segment
        while self.pktStart < len(data):
            try:
              if not res:
                # If next segment goes past end of data, change end of segment to end of data
                segEnd = min(self.pktStart + self.pktSize, len(data))
                seg = data[self.pktStart:segEnd]
                sndChecksum = checksum(seg)
                sndPkt = str(self.seqNum) + str(sndChecksum) + seg
                self.simulator.u_send(sndPkt)  # send data
              else:
                self.simulator.u_send(sndPkt)  #resend
              while True:
                    rcvpkt = self.simulator.u_receive()  # receive ACK or NAK
                    returnSeqNum = rcvpkt[0:1]
                    returnChecksum = rcvpkt[1:33]
                    # If ACK
                    if (((returnChecksum) == str(sndChecksum)) & (str(self.seqNum) == (returnSeqNum))):      
                        self.pktStart += self.pktSize
                        # flip bit
                        self.seqNum = 1 - self.seqNum
                        res = False
                        break
                    else:
                        res = True # If NAK
                        break
            except socket.timeout:
                #Resend if timeout
                self.simulator.u_send(self.sndPkt)
        print("All data sent")
        sys.exit()


if __name__ == "__main__":
    # test out RDTSender
    DATA = bytearray(sys.stdin.read())
    sndr = RDTSender()
    sndr.send(DATA)
