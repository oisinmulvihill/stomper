"""
This is the unittest to verify my stomper module.

The STOMP protocol specification maybe found here:

 * http://stomp.codehaus.org/Protocol

I've looked and the stomp client by Jason R. Briggs and have based the message
generation on how his client did it. The client can be found at the follow 
address however it isn't a dependancy.

 * http://www.briggs.net.nz/log/projects/stomppy


(c) Oisin Mulvihill, 2007-07-26.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
import unittest

import stomper


class StomperTest(unittest.TestCase):


    def testEngine(self):
        """Test the basic state machine responses.
        """
        e = stomper.Engine()

    
    def testFrameUnpack2(self):
        """Testing unpack frame function against MESSAGE
        """
        msg = """MESSAGE
destination:/queue/a
message-id: card_data

hello queue a^@"""

        result = stomper.unpack_frame(msg)
        
        self.assertEquals(result['cmd'], 'MESSAGE')
        self.assertEquals(result['headers']['destination'], '/queue/a')
        self.assertEquals(result['headers']['message-id'], 'card_data')
        self.assertEquals(result['body'], 'hello queue a')
    
    
    def testFrameUnpack1(self):
        """Testing unpack frame function against CONNECTED
        """
        msg = """CONNECTED
session:ID:snorky.local-49191-1185461799654-3:18
"""
        result = stomper.unpack_frame(msg)
        
        self.assertEquals(result['cmd'], 'CONNECTED')
        self.assertEquals(result['headers']['session'], 'ID:snorky.local-49191-1185461799654-3:18')
        self.assertEquals(result['body'], '')

    def testCommit(self):        
        transactionid = '1234'
        correct = "COMMIT\ntransaction: %s\n\n\x00\n" % transactionid
        self.assertEquals(stomper.commit(transactionid), correct)

    def testAbort(self):
        transactionid = '1234'
        correct = "ABORT\ntransaction: %s\n\n\x00\n" % transactionid
        self.assertEquals(stomper.abort(transactionid), correct)

    def testBegin(self):
        transactionid = '1234'
        correct = "BEGIN\ntransaction: %s\n\n\x00\n" % transactionid
        self.assertEquals(stomper.begin(transactionid), correct)
    
    def testAck(self):
        messageid = '1234'
        transactionid = '9876'
        header = 'message-id: %s\ntransaction: %s' % (messageid, transactionid)        
        correct = "ACK\n%s\n\n\x00\n" % header
        self.assertEquals(stomper.ack(messageid, transactionid), correct)

        messageid = '1234'
        correct = "ACK\nmessage-id: %s\n\n\x00\n" % messageid
        self.assertEquals(stomper.ack(messageid), correct)

    def testUnsubscribe(self):
        dest = '/queue/all'
        correct = "UNSUBSCRIBE\ndestination:%s\n\n\x00\n" % dest
        self.assertEquals(stomper.unsubscribe(dest), correct)

    def testSubscribe(self):
        dest, ack = '/queue/all', 'client'
        correct = "SUBSCRIBE\ndestination: %s\nack: %s\n\n\x00\n" % (dest, ack)
        self.assertEquals(stomper.subscribe(dest, ack), correct)

        dest, ack = '/queue/all', 'auto'
        correct = "SUBSCRIBE\ndestination: %s\nack: %s\n\n\x00\n" % (dest, ack)
        self.assertEquals(stomper.subscribe(dest, ack), correct)

        correct = "SUBSCRIBE\ndestination: %s\nack: %s\n\n\x00\n" % (dest, ack)
        self.assertEquals(stomper.subscribe(dest), correct)


    def testConnect(self):
        username, password = 'bob', '123'
        correct = "CONNECT\nlogin:%s\npasscode:%s\n\n\x00\n" % (username, password)
        self.assertEquals(stomper.connect(username, password), correct)
        

    def testDisconnect(self):
        correct = "DISCONNECT\n\n\x00\n"
        self.assertEquals(stomper.disconnect(), correct)


    def testSend(self):
        dest, transactionid, msg = '/queue/myplace', '', '123 456 789'
        correct = "SEND\ndestination: %s\n%s\n%s\x00\n" % (dest, '', msg)
        self.assertEquals(stomper.send(dest, msg, transactionid), correct)

        dest, transactionid, msg = '/queue/myplace', '987', '123 456 789'
        correct = "SEND\ndestination: %s\ntransaction: %s\n%s\x00\n" % (dest, transactionid, msg)
        self.assertEquals(stomper.send(dest, msg, transactionid), correct)
        
        

    
    
if __name__ == "__main__":
    unittest.main()
    
    