"""
A simple twisted STOMP message receiver server.

(c) Oisin Mulvihill, 2007-07-26.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
from __future__ import print_function
import logging

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

import stomper
from stomper import stompbuffer

stomper.utils.log_init(logging.DEBUG)

DESTINATION="/topic/inbox"


class MyStomp(stomper.Engine):
    
    def __init__(self, username='', password=''):
        super(MyStomp, self).__init__()
        self.username = username
        self.password = password
        self.log = logging.getLogger("receiver")


    def connect(self):
        """Generate the STOMP connect command to get a session.
        """
        return stomper.connect(self.username, self.password)


    def connected(self, msg):
        """Once I've connected I want to subscribe to my the message queue.
        """
        super(MyStomp, self).connected(msg)

        self.log.info("connected: session %s" % msg['headers']['session'])
        f = stomper.Frame()
        f.unpack(stomper.subscribe(DESTINATION))
        return f.pack()

        
    def ack(self, msg):
        """Process the message and determine what to do with it.
        """
        self.log.info("RECEIVER - received: %s " % msg['body'])
        
#        return super(MyStomp, self).ack(msg) 

        return stomper.NO_REPONSE_NEEDED
        


class StompProtocol(Protocol):

    def __init__(self, username='', password=''):
        self.sm = MyStomp(username, password)
        self.stompBuffer = stompbuffer.StompBuffer()


    def connectionMade(self):
        """Register with the stomp server.
        """
        cmd = self.sm.connect()
        self.transport.write(cmd)


    def dataReceived(self, data):
        """Use stompbuffer to determine when a complete message has been received. 
        """
        self.stompBuffer.appendData(data)

        while True:
           msg = self.stompBuffer.getOneMessage()
           if msg is None:
               break

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
        print('Lost connection.  Reason:', reason)
    
    
    def clientConnectionFailed(self, connector, reason):
        """Connection failed
        """
        print('Connection failed. Reason:', reason)        
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)



def start(host='localhost', port=61613, username='', password=''):
    """Start twisted event loop and the fun should begin...
    """
    StompClientFactory.username = username
    StompClientFactory.password = password
    reactor.connectTCP(host, port, StompClientFactory())
    reactor.run()


if __name__ == '__main__':
    start()

