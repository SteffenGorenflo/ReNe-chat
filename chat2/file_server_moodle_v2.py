import socket               # Import socket module
import select
import sys
import time
import os
import struct
import math
from threading import Thread
from threading import Event
from operator import itemgetter
from tcpip_packets import *

# TCP Verbindung
class TCP_Connection(object):
    def __init__(self,srcp,dstp):
        self.dst_addr=dstaddr   # Ziel addresse (ip,port)
        self.dstp=dstp          # Ziel Port
        self.srcp=srcp          # Source Port
        self.mss=1000           # Maximum Segment Size
        self.rto=1              # Retransmission timeout (konstant)
        self.state='CLOSED'     # Zustand

        self.tx_next=0          # next segment to transmit
        self.tx_acked=-1        # größtes empfangenes ACK
        self.rx_max=-1          # max segment received in order
        self.tx_max=-1          # maximum byte sent ever
        self.segments_in_flight=[] # segments in flight
                                # list of (info, segment) tupels

        self.cwnd=1             # congestion window
        self.rwnd=8             # receive window
        self.dupACKs=0          # duplicate ACKs
        self.ssthresh=8         # slow start threshold
        self.n_rtx=0            # number of current retransmissions
        self.max_rtx=5          # maximum number of retransmissions
        self.buffered_packets=sorted([],key=itemgetter(0))
                                # buffer for packets received out of order

        self.segment=TCP(srcp,dstp) # TCP object for generating and analyzinig TCP packets
                                    # see tcpip_packet.py

    # print state of connection
    def pr(self):
        print(self.state+', tx_next:',self.tx_next,', tx_max:',self.tx_max,end='')
        print(' tx_acked:',self.tx_acked,', cwnd:',self.cwnd,' flight:',len(self.segments_in_flight))

    # main function to call
    def listen(self):
        print('Listening ....')
        if not self.wait_syn():
            debugmsg('abort wait_syn')
            return False
        self.state = 'ESTABLISHED'
        print('Connection established, waiting for request ...')
        if not self.wait_request():
            debugmsg('abort wait_request')
            return False
        print('Request for',self.num_segments,' segments received')
        print('Sending data...')
        if not self.send_data():
            debugmsg('abort send_data')
            return False
        print('Data transfered, closing connection ...')
        if not self.close():
            debugmsg('abort close')
            return False
        print('Connection closed')
        return True

    # function to establish connection, exit after entering ESTABLISHED state
    def wait_syn(self):
        data = receive_segment(5);
        packetinfo = self.segment.get_info(data)
        debugmsg("received some data from client")
        if not packetinfo == (0,0,1,0,0,0):
            debugmsg("Not correct syn packet. Still waiting")
            self.wait_syn

        debugmsg("received SYN, sending SYN+ACK")
        
        self.rx_max += 1;
        synack = self.segment.gen_packet(seqn=self.tx_next,syn=1,ack=1,ackn=self.rx_max+1)

        self.send_packet(synack)

        debugmsg("waiting for ACK")
        return self.wait_ack()
    # receive and acknowledge a request 
    def wait_request(self):
        data = receive_segment(5);
        packetinfo = self.segment.get_info(data)
        debugmsg("waiting for a request")
        if not packetinfo == (self.rx_max + 1, self.tx_acked + 1, 0 , 0 ,4, 0):
            self.wait_request

        debugmsg("Got request")
        self.rx_max +=1

        tcpp=self.segment.unpack(data)
        self.num_segments = struct.unpack("i",tcpp.payload)[0]

        debugmsg("Send Ack")
        self.send_ack()
        return True


    def wait_ack(self):
        data = receive_segment(5);
        packetinfo = self.segment.get_info(data)
        self.segments_in_flight.pop(0)
        self.tx_acked += 1
        self.rx_max += 1
        debugmsg("ACK recieved")

        return True

    # send the data, main function
    def send_data(self):
        #remove first item in list
        self.segments_in_flight.pop(0)
        for x in range(0, self.num_segments):
            payload = self.gen_data()
            self.tx_next += 1
            packet=self.segment.gen_packet(seqn=self.tx_next,ackn=self.rx_max+1,payload=payload)
            self.send_packet(packet)
            self.wait_ack()
        return True

    # function to execute closing procedure
    def close(self):
        close = self.segment.gen_packet(fin=1,seqn=self.tx_next,ackn=self.rx_max+1)
        self.send_packet(close)
        self.wait_ack()

        return True


    # generate a packet (header#payload),
    # payload should be the repeated segment number
    def gen_data(self):
        return os.urandom(1000)
        
    # send an ack: recommended to send all ACK using this function
    def send_ack(self):
        packet=self.segment.gen_packet(seqn=self.tx_next,ackn=self.rx_max+1,ack=1)
        self.tx_next += 1
        self.send_packet(packet)
    
    
    # implement a function to trigger retransmits
    # function should return false in number of retransmissions is exceeded
    def rtx_packet(self):
        pass    # TODO: Schritt 1-4, Aufgabe 4


    # implement a function for fast retransmit only for Reno version
    def fast_rtx(self):
        pass    # TODO: Aufgabe 4
        

    # this function should be used to send packets with payload
    # Funktion kann unverändert verwendet werden.
    # Je nach Implementierung kann eine Adaption vorgenommen werden
    def send_packet(self,packet):
        self.segments_in_flight.append((self.segment.get_info(packet),packet))
        send_segment(packet,self.segment.get_info(packet))

    def printself(self):
        debugmsg("self.tx_next = " + str(self.tx_next))
        debugmsg("self.tx_acked = " +str(self.tx_acked))
        debugmsg("self.rx_max = " +  str(self.rx_max))  
        debugmsg("self.tx_max = " +str(self.tx_max))



# function to receive packet from UDP socket, print the information and extract TCP packet
# Funktion kann unverändert verwendet werden
def receive_segment(rto):
    # function times out after rto
    s.settimeout(rto)
    # receive packet
    try:
        packet, addr = s.recvfrom(2048)    # read from socket
    except socket.timeout:
        # in case of error or timeout return []
        return []
    except socket.error as e:
        print(e)
        return []
    # extract header fields from binary packet
    iph=ipo.unpack(packet)
    if iph.dst!=my_v_ip:
        print('Error: IP packet not addressed to me',iph.dst)
        return
    # extract information from TCP Packet
    # packet[20:]:packet without 20 Bytes IP header
    info=tcpo.get_info(packet[20:])
    print_packet('IN: ',ipo.id,info)
    # return TCP packet
    return packet[20:]
        


# this function sends packets on the UDP socket
# Funktion kann unverändert verwendet werden
def send_segment(packet,info):
    print_packet('OUT:',ipo.id,info)
    # create IP header
    iph=ipo.pack()
    # add IP header
    packet=iph+packet
    # send packet
    s.sendto(packet,(dst_ip,dst_port))


# function to print information for a packet
def print_packet(s,pid,info):
    print(s+' '+my_time()+' ID:'+str(ipo.id),end='')
    print(' SEQ:'+str(info[0])+'-'+str(info[0]+info[4]/1000),end='')
    print(' Payload: '+str(info[4]),end='')
    print(' ACK:'+str(info[1])+' ',end='')
    if info[2]:
        print('S',end='')
    if info[3]:
        print('A',end='')
    if info[5]:
        print('F',end='')
    print()
        

def my_time():
    return '{:+3.3f}'.format(time.time()%1e3)

# the server, started as a thread
def my_file_server():
    global goon
    conn=TCP_Connection(my_v_port,dst_v_port)
    ok=conn.listen()
    goon=False

def debugmsg(msg):
    if (debug):
        print('[debug_server]: ' + msg)



# global data
goon=True               # Threads stop if goon==0
debug=False

# real and virtual addresses and ports
# TODO: Adressen bei Bedarf richtig konfigurieren, insbesondere bei Aufgabe 5 und 6
my_port=6000
dst_port=5000
my_ip='127.0.0.1'
dst_ip='127.0.0.1'
my_v_ip='141.37.168.1'
dst_v_ip='141.37.168.2'
my_v_port=100
# sollte nach Empfang des SYN-Pakets gesetzt werden, spielt hier aber keine Rolle
dst_v_port=0
dstaddr=(dst_ip,dst_port)


# open a udp socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((my_ip,my_port))
s.settimeout(30) # set time out to 30 seconds

# generic IP object for generating and extracting IP headers
ipo=IP(my_v_ip,dst_v_ip)

tcpo=TCP(0,0)
tcpo.pack()

# thread for the client
t_file=Thread(target=my_file_server)
t_file.start()

# possibility to quit
while goon:
    time.sleep(1)
    action=input('Enter Action (<Q>)\n')
    if action=='Q':
        print('Quitting')
        goon=False





        
        
