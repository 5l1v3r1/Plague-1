from twisted.internet.protocol import Factory
from plague.utils import *
from plague.protocol import *

class PlagueFactory(Factory):
    def __init__(self):
        self.peers = {}
        self.nodeid = utils().uuid()

    def buildProtocol(self, addr):
        return PlagueProtocol(self, 2)