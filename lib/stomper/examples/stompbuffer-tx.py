"""
A simple twisted STOMP message sender.

(c) Oisin Mulvihill, 2007-07-26.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
from __future__ import print_function
import logging

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

import stomper
from stomper import stompbuffer


stomper.utils.log_init(logging.DEBUG)

DESTINATION="/topic/inbox"


class StompProtocol(Protocol, stomper.Engine):

    def __init__(self, username='', password=''):
        stomper.Engine.__init__(self)
        self.username = username
        self.password = password
        self.counter = 1
        self.log = logging.getLogger("sender")
        self.stompBuffer = stompbuffer.StompBuffer()


    def connected(self, msg):
        """Once I've connected I want to subscribe to my the message queue.
        """
        stomper.Engine.connected(self, msg)

        self.log.info("Connected: session %s. Beginning say hello." % msg['headers']['session'])
        
        def setup_looping_call():
            lc = LoopingCall(self.send)
            lc.start(2)
            
        reactor.callLater(1, setup_looping_call)

        f = stomper.Frame()
        f.unpack(stomper.subscribe(DESTINATION))

        # ActiveMQ specific headers:
        #
        # prevent the messages we send comming back to us.
        f.headers['activemq.noLocal'] = 'true'
        
        return f.pack()

        
    def ack(self, msg):
        """Processes the received message. I don't need to 
        generate an ack message.
        
        """
        self.log.info("SENDER - received: %s " % msg['body'])
        return stomper.NO_REPONSE_NEEDED


    def send(self):
        """Send out a hello message periodically.
        """
        self.log.info("Saying hello (%d)." % self.counter)

        f = stomper.Frame()
        f.unpack(stomper.send(DESTINATION, 'hello there (%d)' % self.counter))

        self.counter += 1        

        # ActiveMQ specific headers:
        #
        #f.headers['persistent'] = 'true'

        self.transport.write(f.pack())


    def connectionMade(self):
        """Register with stomp server.
        """
        cmd = stomper.connect(self.username, self.password)
        self.transport.write(cmd)


    def dataReceived(self, data):
        """Use stompbuffer to determine when a complete message has been received. 
        """
        self.stompBuffer.appendData(data)

        while True:
           msg = self.stompBuffer.getOneMessage()
           if msg is None:
               break

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

