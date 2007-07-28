"""
A simple twisted STOMP message sender.

(c) Oisin Mulvihill, 2007-07-26.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

import stomper

DESTINATION="/queue/my_dest"


class StompProtocol(Protocol, stomper.Engine):

    def __init__(self, username='', password=''):
        stomper.Engine.__init__(self)
        self.username = username
        self.password = password


    def connected(self, msg):
        """Once I've connected I want to subscribe to my the message queue.
        """
        stomper.Engine.connected(self, msg)

        print "Connected: session %s. Begining say hello." % msg['headers']['session']
        lc = LoopingCall(self.send)
        lc.start(1)
        
        return stomper.subscribe(DESTINATION)

        
    def ack(self, msg):
        """Processes the received message. I don't need to 
        generate an ack message.
        
        """
        print "SENDER - received: ", msg['body']
        return stomper.NO_REPONSE_NEEDED


    def send(self):
        """Send out a hello message periodically.
        """
        print "Saying hello."
        self.transport.write(stomper.send(DESTINATION, 'hello there'))


    def connectionMade(self):
        """Register with stomp server.
        """
        cmd = stomper.connect(self.username, self.password)
        self.transport.write(cmd)


    def dataReceived(self, data):
        """Data received, react to it and respond if needed.
        """
        msg = stomper.unpack_frame(data)
        
        returned = self.react(msg)
        if returned:
            self.transport.write(returned)



class StompClientFactory(ReconnectingClientFactory):
    
    # Will be set up before the factory is created.
    username, password = '', ''
    
    def buildProtocol(self, addr):
        return StompProtocol(self.username, self.password)
    
    
    def clientConnectionLost(self, connector, reason):
        """Lost connection
        """
        print 'Lost connection.  Reason:', reason
    
    
    def clientConnectionFailed(self, connector, reason):
        """Connection failed
        """
        print 'Connection failed. Reason:', reason        



def start(host='localhost', port=61613, username='', password=''):
    """Start twisted event loop and the fun should begin...
    """
    StompClientFactory.username = username
    StompClientFactory.password = password
    reactor.connectTCP(host, port, StompClientFactory())
    reactor.run()


if __name__ == '__main__':
    start()

