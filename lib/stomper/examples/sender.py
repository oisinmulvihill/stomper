"""
A simple twisted STOMP message sender.

(c) Oisin Mulvihill, 2007-07-26.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
from __future__ import print_function
from builtins import str
import uuid
import logging
import itertools

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

import stomper

stomper.utils.log_init(logging.DEBUG)

DESTINATION="/topic/inbox"


class StompProtocol(Protocol, stomper.Engine):

    def __init__(self, username='', password=''):
        stomper.Engine.__init__(self)
        self.username = username
        self.password = password
        self.counter = itertools.count(0)
        self.log = logging.getLogger("sender")
        self.senderID = str(uuid.uuid4())


    def connected(self, msg):
        """Once I've connected I want to subscribe to my the message queue.
        """
        stomper.Engine.connected(self, msg)

        self.log.info("senderID:%s Connected: session %s." % (
            self.senderID, 
            msg['headers']['session'])
        )

        # I originally called loopingCall(self.send) directly, however it turns
        # out that we had not fully subscribed. This meant we did not receive 
        # out our first send message. I fixed this by using reactor.callLater
        # 
        #
        def setup_looping_call():
            lc = LoopingCall(self.send)
            lc.start(2)
            
        reactor.callLater(1, setup_looping_call)

        f = stomper.Frame()
        f.unpack(stomper.subscribe(DESTINATION))

        # ActiveMQ specific headers:
        #
        # prevent the messages we send coming back to us.
        f.headers['activemq.noLocal'] = 'true'
        
        return f.pack()

        
    def ack(self, msg):
        """Processes the received message. I don't need to 
        generate an ack message.
        
        """
        self.log.info("senderID:%s Received: %s " % (self.senderID, msg['body']))
        return stomper.NO_REPONSE_NEEDED


    def send(self):
        """Send out a hello message periodically.
        """
        counter = next(self.counter)
        
        self.log.info("senderID:%s Saying hello (%d)." % (self.senderID, counter))

        f = stomper.Frame()
        f.unpack(stomper.send(DESTINATION, '(%d) hello there from senderID:<%s>' % (
            counter, 
            self.senderID
        )))

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
        """Data received, react to it and respond if needed.
        """
        #print "sender dataReceived: <%s>" % data

        msg = stomper.unpack_frame(data)
        
        returned = self.react(msg)

        #print "sender returned: <%s>" % returned

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

