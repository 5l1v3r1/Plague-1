from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet import reactor
from plague.protocol import *
from plague.factory import *
import sys

factory = PlagueFactory()
port = sys.argv[1]

print(f'My ID: {factory.nodeid}')
print(f'Binding to port {port}')

# create a server
endpoint = TCP4ServerEndpoint(reactor, int(port))
endpoint.listen(factory)

# create a client
BOOTSTRAP_LIST = [ 
    f'127.0.0.1:{str(int(port) - 1)}',
    f'127.0.0.1:{str(int(port) + 1)}',
    f'127.0.0.1:{str(int(port) + 2)}',
]

for bootstrap in BOOTSTRAP_LIST:
    print(f'Connecting to {bootstrap}')

    node_host, node_port = bootstrap.split(":")
    point = TCP4ClientEndpoint(reactor, node_host, int(node_port))
    d = connectProtocol(point, PlagueProtocol(factory, 2))
    d.addCallback(lambda p: p.send_helo())

reactor.run()