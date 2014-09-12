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
import pprint
import unittest

import stomper.stomp_10 as stomper


class TestEngine(stomper.Engine):
    """Test that these methods are called by the default engine.
    """
    def __init__(self):
        super(TestEngine, self).__init__()
        self.ackCalled = False
        self.errorCalled = False
        self.receiptCalled = False

    def ack(self, msg):
        super(TestEngine, self).ack(msg)
        self.ackCalled = True
        return 'ack'

    def error(self, msg):
        super(TestEngine, self).error(msg)
        self.errorCalled = True
        return 'error'

    def receipt(self, msg):
        super(TestEngine, self).receipt(msg)
        self.receiptCalled = True
        return 'receipt'


class Stomper10Test(unittest.TestCase):

    def testEngineToServerMessages(self):
        """Test the state machines reaction
        """
        e = TestEngine()

        # React to a message which should be an ack:
        msg = stomper.Frame()
        msg.cmd = 'MESSAGE'
        msg.headers = {
            'destination:': '/queue/a',
            'message-id:': 'some-message-id'
        }
        msg.body = "hello queue a"

        rc = e.react(msg.pack())
        self.assertEquals(rc, 'ack')
        self.assertEquals(e.ackCalled, True)

        # React to an error:
        error = stomper.Frame()
        error.cmd = 'ERROR'
        error.headers = {'message:': 'malformed packet received!'}
        error.body = """The message:
-----
MESSAGE
destined:/queue/a

Hello queue a!
-----
Did not contain a destination header, which is required for message propagation.
\x00
        """

        rc = e.react(error.pack())
        self.assertEquals(rc, 'error')
        self.assertEquals(e.errorCalled, True)

        # React to an receipt:
        receipt = stomper.Frame()
        receipt.cmd = 'RECEIPT'
        receipt.headers = {'receipt-id:': 'message-12345'}

        rc = e.react(receipt.pack())
        self.assertEquals(rc, 'receipt')
        self.assertEquals(e.receiptCalled, True)

    def testEngine(self):
        """Test the basic state machine.
        """
        e = stomper.Engine(testing=True)

        # test session connected message:
        msg = """CONNECTED
session:ID:snorky.local-49191-1185461799654-3:18

\x00
"""
        result = stomper.unpack_frame(msg)
        correct = ''
        returned = e.react(result)
        self.assertEquals(returned, correct)

        # test message:
        msg = """MESSAGE
destination: /queue/a
message-id: some-message-id

hello queue a

\x00
"""
        returned = e.react(msg)
        correct = 'ACK\nmessage-id: some-message-id\n\n\x00\n'
        self.assertEquals(returned, correct)

        # test error:
        msg = """ERROR
message:some error

There was a problem with your last message

\x00
"""
        returned = e.react(msg)
        correct = 'error'
        self.assertEquals(returned, correct)

        # test receipt:
        msg = """RECEIPT
message-id: some-message-id

\x00
"""
        returned = e.react(msg)
        correct = 'receipt'
        self.assertEquals(returned, correct)

    def testFramepack1(self):
        """Testing pack, unpacking and the Frame class.
        """
        # Check bad frame generation:
        frame = stomper.Frame()

        def bad():
            frame.cmd = 'SOME UNNOWN CMD'

        self.assertRaises(stomper.FrameError, bad)

        # Generate a MESSAGE frame:
        frame = stomper.Frame()
        frame.cmd = 'MESSAGE'
        frame.headers['destination'] = '/queue/a'
        frame.headers['message-id'] = 'card_data'
        frame.body = "hello queue a"
        result = frame.pack()

#        print "\n-- result " + "----" * 10
#        pprint.pprint(result)
#        print

        # Try bad message unpack catching:
        bad_frame = stomper.Frame()
        self.assertRaises(stomper.FrameError, bad_frame.unpack, None)
        self.assertRaises(stomper.FrameError, bad_frame.unpack, '')

        # Try to read the generated frame back in
        # and then check the variables are set up
        # correctly:
        frame2 = stomper.Frame()
        frame2.unpack(result)

        self.assertEquals(frame2.cmd, 'MESSAGE')
        self.assertEquals(frame2.headers['destination'], '/queue/a')
        self.assertEquals(frame2.headers['message-id'], 'card_data')
        self.assertEquals(frame2.body, 'hello queue a')
        result = frame2.pack()

        correct = "MESSAGE\ndestination:/queue/a\nmessage-id:card_data\n\nhello queue a\x00\n"

#        print "result: "
#        pprint.pprint(result)
#        print
#        print "correct: "
#        pprint.pprint(correct)
#        print
#
        self.assertEquals(result, correct)

        result = stomper.unpack_frame(result)

        self.assertEquals(result['cmd'], 'MESSAGE')
        self.assertEquals(result['headers']['destination'], '/queue/a')
        self.assertEquals(result['headers']['message-id'], 'card_data')
        self.assertEquals(result['body'], 'hello queue a')

    def testFramepack2(self):
        """Testing pack, unpacking and the Frame class.
        """
        # Check bad frame generation:
        frame = stomper.Frame()
        frame.cmd = 'DISCONNECT'
        result = frame.pack()
        correct = 'DISCONNECT\n\n\x00\n'
        self.assertEquals(result, correct)

    def testFrameUnpack2(self):
        """Testing unpack frame function against MESSAGE
        """
        msg = """MESSAGE
destination:/queue/a
message-id: card_data

hello queue a"""

        result = stomper.unpack_frame(msg)

        self.assertEquals(result['cmd'], 'MESSAGE')
        self.assertEquals(result['headers']['destination'], '/queue/a')
        self.assertEquals(result['headers']['message-id'], 'card_data')
        self.assertEquals(result['body'], 'hello queue a')

    def testFrameUnpack3(self):
        """Testing unpack frame function against CONNECTED
        """
        msg = """CONNECTED
session:ID:snorky.local-49191-1185461799654-3:18
"""
        result = stomper.unpack_frame(msg)

        self.assertEquals(result['cmd'], 'CONNECTED')
        self.assertEquals(result['headers']['session'], 'ID:snorky.local-49191-1185461799654-3:18')
        self.assertEquals(result['body'], '')

    def testBugInFrameUnpack1(self):
        msg = """MESSAGE
destination:/queue/a
message-id: card_data

hello queue a

\x00
"""
        result = stomper.unpack_frame(msg)

        self.assertEquals(result['cmd'], 'MESSAGE')
        self.assertEquals(result['headers']['destination'], '/queue/a')
        self.assertEquals(result['headers']['message-id'], 'card_data')
        self.assertEquals(result['body'], 'hello queue a')

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
        correct = "SEND\ndestination: %s\n\n%s\x00\n" % (dest, msg)
        result = stomper.send(dest, msg, transactionid)

#        print "result: "
#        pprint.pprint(result)
#        print
#        print "correct: "
#        pprint.pprint(correct)
#        print

        self.assertEquals(result, correct)

        dest, transactionid, msg = '/queue/myplace', '987', '123 456 789'
        correct = "SEND\ndestination: %s\ntransaction: %s\n\n%s\x00\n" % (dest, transactionid, msg)
        self.assertEquals(stomper.send(dest, msg, transactionid), correct)

if __name__ == "__main__":
    unittest.main()
