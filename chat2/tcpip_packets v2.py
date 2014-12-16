import socket               # Import socket module
import struct

class layer():
    pass

# Klasse zum Erstellen und extrahieren von IP-Headern
class IP(object):
    def __init__(self, source, destination):
        self.version = 4
        self.ihl = 5 # Internet Header Length
        self.tos = 0 # Type of Service
        self.tl = 0 # total length will be filled by kernel
        self.id = 0
        self.flags = 0
        self.offset = 0
        self.ttl = 255
        self.protocol = socket.IPPROTO_TCP
        self.checksum = 0 # not used
        self.source = socket.inet_aton(source)
        self.destination = socket.inet_aton(destination)

    # liefert IP-Header zum Übertragen im UDP Socket (oder auf RAW Sockets)    
    def pack(self):
        ver_ihl = (self.version << 4) + self.ihl
        flags_offset = (self.flags << 13) + self.offset
        ip_header = struct.pack("!BBHHHBBH4s4s",
            ver_ihl,
            self.tos,
            self.tl,
            self.id,
            flags_offset,
            self.ttl,
            self.protocol,
            self.checksum,
            self.source,
            self.destination)
        return ip_header
    
    # extrahiert IP header aus ersten 20 Byte eines empfangenen Pakets
    def unpack(self, packet):
        _ip = layer()
        _ip.ihl = (packet[0] & 0xf) * 4
        iph = struct.unpack("!BBHHHBBH4s4s", packet[:_ip.ihl])
        _ip.ver = iph[0] >> 4
        _ip.tos = iph[1]
        _ip.length = iph[2]
        _ip.ids = iph[3]
        _ip.flags = iph[4] >> 13
        _ip.offset = iph[4] & 0x1FFF
        _ip.ttl = iph[5]
        _ip.protocol = iph[6]
        _ip.checksum = hex(iph[7])
        _ip.src = socket.inet_ntoa(iph[8])
        _ip.dst = socket.inet_ntoa(iph[9])
        _ip.list = [
            _ip.ihl,
            _ip.ver,
            _ip.tos,
            _ip.length,
            _ip.ids,
            _ip.flags,
            _ip.offset,
            _ip.ttl,
            _ip.protocol,
            _ip.src,
            _ip.dst]
        return _ip

    # einfache Funktion zum Generieren kontinuierlicher Header aus einem Objekt
    def gen_header(self):
        self.id+=1
        return(self.pack())

    # Extrahieren der wesentlichen Informationen eines Pakets
    def get_info(self,packet):
        self.unpack(packet)
        return (self.src, self.dst, self.ids)

# Klasse zum Erstellen und extrahieren von TCP-Headern
class TCP(object):
    def __init__(self, srcp, dstp):
        self.srcp = srcp
        self.dstp = dstp
        self.seqn = 0
        self.ackn = 0
        self.offset = 5 # Data offset: 5x4 = 20 bytes
        self.reserved = 0
        self.urg = 0
        self.ack = 0
        self.psh = 0
        self.rst = 0
        self.syn = 0
        self.fin = 0
        self.window = socket.htons(5840)
        self.checksum = 0
        self.urgp = 0
        self.payload = ""

    # binäres TCP-Pakte erstellen
    def pack(self):
        data_offset = (self.offset << 4) + 0
        flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5)
        tcp_header = struct.pack('!HHLLBBHHH',
            self.srcp,
            self.dstp,
            self.seqn,
            self.ackn,
            data_offset,
            flags,
            self.window,
            self.checksum,
            self.urgp)
        return tcp_header

    # TCP Header und Payload aus binärem TCP Paket
    def unpack(self, packet):
        cflags = { # Control flags
            32:"U",
            16:"A",
            8:"P",
            4:"R",
            2:"S",
            1:"F"}
        _tcp = layer()
        _tcp.thl = ((packet[12])>>4) * 4
        _tcp.options = packet[20:_tcp.thl]
        _tcp.payload = packet[_tcp.thl:]
        tcph = struct.unpack("!HHLLBBHHH", packet[:20])
        _tcp.srcp = tcph[0] # source port
        _tcp.dstp = tcph[1] # destination port
        _tcp.seq = tcph[2] # sequence number
        _tcp.ack = tcph[3] # acknowledgment number
        _tcp.flags = ""
        for f in cflags:
            if tcph[5] & f:
                _tcp.flags+=cflags[f]
        _tcp.window = tcph[6] # window
        _tcp.checksum = hex(tcph[7]) # checksum
        _tcp.urg = tcph[8] # urgent pointer
        _tcp.list = [
            _tcp.srcp,
            _tcp.dstp,
            _tcp.seq,
            _tcp.ack,
            _tcp.thl,
            _tcp.flags,
            _tcp.window,
            _tcp.checksum,
            _tcp.urg,
            _tcp.options]
        _tcp.syn=_tcp.flags.find("S") != -1
        _tcp.isACK=_tcp.flags.find("A") != -1
        _tcp.fin=_tcp.flags.find("F") != -1
        return _tcp

    # Paket aus wesentlichen Informationen generieren
    def gen_packet(self,seqn,ackn,syn,fin,ack,payload):
        self.seqn=seqn
        self.ackn=ackn
        self.syn=syn
        self.ack=ack
        self.fin=fin
        self.payload=payload
        return self.pack()+payload

    # wesentliche Info zu einem Paket
    def get_info(self,packet):
        tcpp=self.unpack(packet)
        return (tcpp.seq,tcpp.ack,tcpp.syn,tcpp.isACK,len(tcpp.payload),tcpp.fin)

