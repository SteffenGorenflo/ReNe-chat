from errno import ECONNREFUSED
from functools import partial
from multiprocessing import Pool
import socket

NUM_CORES = 4

def ping(host, port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	
	print("send to socket: " + str(port))
	sock.settimeout(1)
	sock.sendto("HELLO".encode("UTF-8"),(host,port))
	
	try:
		data, addr = sock.recvfrom(250)
		print("received: " + str(data))
		print(str(addr))
		return port
	except socket.error as serr:
		print("not reachable: " + str(port) + " because of " + str(serr))


def scan_ports(host):
	p = Pool(NUM_CORES)
	ping_host = partial(ping, host)
	return filter(bool, p.map(ping_host, range(1, 50)))


def main(host=None):
	if host is None:
		host = "141.37.168.26"

	print("\nScanning ports on " + host + " ...")
	ports = list(scan_ports(host))
	print("\nDone.")

	print(str(len(ports)) + " ports available.")
	print(ports)


if __name__ == "__main__":
	main()