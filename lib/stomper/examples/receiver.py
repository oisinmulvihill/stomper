"""
A simple twisted STOMP message receiver server.

(c) Oisin Mulvihill, 2007-07-26.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

import stomper

DESTINATION="/queue/my_dest"

class MyStomp(stomper.Engine):
    
    def __init__(self, username='', password=''):
        super(MyStomp, self).__init__()
        self.username = username
        self.password = password
        self.states['MESSAGE'] = self.message


    def connect(self):
        """Generate the STOMP connect command to get a session.
        """
        return stomper.connect(self.username, self.password)


    def connected(self, msg):
        """Once I've connected I want to subscribe to my the message queue.
        """
        super(MyStomp, self).connected(msg)

        print "connected: session %s" % msg['headers']['session']
        return stomper.subscribe(DESTINATION)

        
    def message(self, msg):
        """Process the message and determine what to do with it.
        """
        print "received: ", msg['body']
        return stomper.NO_REPONSE_NEEDED
        


class StompProtocol(Protocol):

    def __init__(self, username='', password=''):
        self.sm = MyStomp(username, password)


    def connectionMade(self):
        """Register with the stomp server.
        """
        cmd = self.sm.connect()
        self.transport.write(cmd)

    
    def dataReceived(self, data):
        """Data received, react to it and respond if needed.
        """
        msg = stomper.unpack_frame(data)
        
        returned = self.sm.react(msg)
        if returned:
            self.transport.write(returned)



class StompClientFactory(ReconnectingClientFactory):
    
    # Will be set up before the factory is created.
    username, password = '', ''
    
    def startedConnecting(self, connector):
        """Started to connect.
        """


    def buildProtocol(self, addr):
        """Transport level connected now create the communication protocol.
        """
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

