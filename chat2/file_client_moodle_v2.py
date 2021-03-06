import socket               # Import socket module
import select
import sys
import time
import struct
import math
from threading import Thread
from threading import Event
from operator import itemgetter
from tcpip_packets import *


# TCP Verbindung
class TCP_Connection(object):
	def __init__(self,srcp,dstp,dstaddr):
		self.dst_addr=dstaddr   # Ziel addresse (ip,port)
		self.dstp=dstp          # Ziel Port
		self.srcp=srcp          # Source Port
		self.mss=1000           # Maximum Segment Size
		self.rto=1              # Retransmission timeout (konstant)
		self.state='CLOSED'     # Zustand
		self.maxSendTries=5     # 

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

   
	# send request, get ACK, retrieve data
	def request_data(self,n):
		self.num_segments=n
		if not self.connect():
			print('Connection establihsment failed')
			return False
		self.state='ESTABLISHED'
		print('Connection established, sending request')
		if not self.send_request():
			debugmsg('sending request failed')
			return False
		if not self.wait_ack():
			return False
		print('Request acked, retreiving data ...')
		if not self.receive_data():
			return False
			print('Data received, closing connection')
		return self.close()

	# establish TCP connection
	def connect(self):
		if not self.send_syn():
			return False
		if not self.wait_ack():
			return False
		return True

	def send_syn(self):
		debugmsg('Sending syn')
		packet=self.segment.gen_packet(seqn=self.tx_next,syn=1)
		self.tx_next += 1
		return self.send_packet(packet)

	# send the request containing the number of segments
	def send_request(self):
		payload=struct.pack('i',self.num_segments)
		
		request = self.segment.gen_packet(seqn=self.tx_next,payload=payload,ackn=self.rx_max+1)
		self.tx_next += 1
		return self.send_packet(request)

	# function to receive data
	def receive_data(self):
		while goon:

			data = receive_segment(5)
			packetinfo = self.segment.get_info(data)
			debugmsg("Data received")
			self.rx_max += 1

			debugmsg("Send ACK")
			self.send_ack()

			#remove last ack
			self.segments_in_flight.pop(0)
			if packetinfo[5]:
				return True
		return False

	# function to execute closing procedure
	def close(self):
		debugmsg("close connection")
		return True

	# send an ack: recommended to send all ACK using this function
	def send_ack(self):
		packet=self.segment.gen_packet(seqn=self.tx_next,ackn=self.rx_max+1,ack=1)
		self.tx_next += 1
		self.send_packet(packet)


	# implement a function to trigger retransmits
	# function should return false in number of retransmissions is exceeded
	def rtx_packet(self):
		pass    # TODO: Schritt 1-3

	# wait for ACKs (SYNACK, ACK for request), generate ACK for SYNACK
	def wait_ack(self):
		data = receive_segment(5)
		packetinfo = self.segment.get_info(data)

		if not packetinfo[1]:
			self.wait_ack()

		# remove first item in list
		self.segments_in_flight.pop(0)
		self.tx_acked += 1
		self.rx_max += 1
		#SYN/ACK PACKET
		if packetinfo[1] and packetinfo[2]:
			debugmsg('Received SYN+ACK, Sending ACK')
			self.send_ack()
			self.segments_in_flight.pop(0)
		# this function should be used to put them on the UDP socket

		return True

	# this function should be used to send packets with payload
	# Funktion kann unverändert verwendet werden.
	# Je nach Implementierung kann eine Adaption vorgenommen werden
	def send_packet(self,packet):
		self.segments_in_flight.append((self.segment.get_info(packet),packet))
		return send_segment(packet,self.segment.get_info(packet))


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
	try:
		s.sendto(packet,(dst_ip,dst_port))
	except socket.error as e:
		return False
	return True
	

# function to print information for a packet
def print_packet(s, pid,info):
	print(s+' '+my_time()+' ID:'+str(pid),end='')
	print(' SEQ:'+str(info[0])+'-'+str(info[0]+info[4]),end='')
	print(' Payload: '+str(info[4]),end='')
	print(' ACK:'+str(info[1])+' ',end='')
	if info[2]:
		print('S',end='')
	if info[3]:
		print('A',end='')
	if info[5]:
		print('F',end='')
	print()
	
# get time in acceptable format
def my_time():
	return '{:+3.3f}'.format(time.time()%1e3)

# the client, started as a thread
def my_file_client():
	conn=TCP_Connection(my_v_port,dst_v_port,dest_addr)
	if conn.request_data(num_segments):
		print('Retrieved file and close connection')
	else:
		print('Failed')
	goon=False

def debugmsg(msg):
	if (debug):
		print('[debug_client]: ' + msg)



# global data
goon=True               # Threads stop if goon==0
debug=False


# real and virtual addresses and port
# TODO: Adressen bei Bedarf richtig konfigurieren
my_port=5000
dst_port=6000
my_ip='127.0.0.1'
dst_ip='127.0.0.1'
my_v_ip='141.37.168.2'
dst_v_ip='141.37.168.1'
my_v_port=1000
dst_v_port=100
dest_addr=(dst_ip,dst_port)

# number of segments requested
# TODO: für Schritt 4 anpassen
num_segments=10

# open a udp socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((my_ip,my_port))
s.settimeout(20)

# generic IP object for generating and extracting IP headers
ipo=IP(my_v_ip,dst_v_ip)

# generic TCP object for generating and extracting IP headers
tcpo=TCP(0,0)
tcpo.pack()

# thread for the client
t_file=Thread(target=my_file_client)
t_file.start()

# possibility to quit
while goon:
	time.sleep(1)
	action=input('Enter Action (<Q>)\n')
	if action=='Q':
		print('Quitting')
		goon=False



		
		
