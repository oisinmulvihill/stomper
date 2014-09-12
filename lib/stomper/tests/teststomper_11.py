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

import stomper
#.stomp_11 as stomper


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


class Stomper11Test(unittest.TestCase):

    def testEngineToServerMessages(self):
        """Test the state machines reaction
        """
        e = TestEngine()

        # React to a message which should be an ack:
        msg = stomper.Frame()
        msg.cmd = 'MESSAGE'
        msg.headers = {
            'subscription': 1,
            'destination:': '/queue/a',
            'message-id:': 'some-message-id',
            'content-type': 'text/plain',
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
version:1.1
session:ID:snorky.local-49191-1185461799654-3:18

\x00
"""
        result = stomper.unpack_frame(msg)
        correct = ''
        returned = e.react(result)
        self.assertEquals(returned, correct)

        # test message:
        msg = """MESSAGE
subscription:1
destination:/queue/a
message-id:some-message-id
content-type:text/plain

hello queue a

\x00
"""
        returned = e.react(msg)
        correct = 'ACK\nsubscription:1\nmessage-id:some-message-id\n\n\x00\n'
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
message-id:some-message-id

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
message-id:card_data

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
version:1.1
session:ID:snorky.local-49191-1185461799654-3:18
"""
        result = stomper.unpack_frame(msg)

        self.assertEquals(result['cmd'], 'CONNECTED')
        self.assertEquals(result['headers']['session'], 'ID:snorky.local-49191-1185461799654-3:18')
        self.assertEquals(result['body'], '')

    def testBugInFrameUnpack1(self):
        msg = """MESSAGE
destination:/queue/a
message-id:card_data

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
        correct = "COMMIT\ntransaction:%s\n\n\x00\n" % transactionid
        self.assertEquals(stomper.commit(transactionid), correct)

    def testAbort(self):
        transactionid = '1234'
        correct = "ABORT\ntransaction:%s\n\n\x00\n" % transactionid
        self.assertEquals(stomper.abort(transactionid), correct)

    def testBegin(self):
        transactionid = '1234'
        correct = "BEGIN\ntransaction:%s\n\n\x00\n" % transactionid
        self.assertEquals(stomper.begin(transactionid), correct)

    def testAck(self):
        subscription = '1'
        messageid = '1234'
        transactionid = '9876'
        header = 'subscription:%s\nmessage-id:%s\ntransaction:%s' % (
            subscription, messageid, transactionid)
        correct = "ACK\n%s\n\n\x00\n" % header
        actual = stomper.ack(messageid, subscription, transactionid)
        self.assertEquals(actual, correct)

        subscription = '1'
        messageid = '1234'
        correct = "ACK\nsubscription:%s\nmessage-id:%s\n\n\x00\n" % (
            subscription, messageid)
        self.assertEquals(stomper.ack(messageid, subscription), correct)

    def testNack(self):
        subscription = '1'
        messageid = '1234'
        transactionid = '9876'
        header = 'subscription:%s\nmessage-id:%s\ntransaction:%s' % (
            subscription, messageid, transactionid)
        correct = "NACK\n%s\n\n\x00\n" % header
        actual = stomper.nack(messageid, subscription, transactionid)
        self.assertEquals(actual, correct)

        subscription = '1'
        messageid = '1234'
        correct = "NACK\nsubscription:%s\nmessage-id:%s\n\n\x00\n" % (
            subscription, messageid)
        self.assertEquals(stomper.nack(messageid, subscription), correct)

    def testUnsubscribe(self):
        subscription = '1'
        correct = "UNSUBSCRIBE\nid:%s\n\n\x00\n" % subscription
        self.assertEquals(stomper.unsubscribe(subscription), correct)

    def testSubscribe(self):
        dest, ack = '/queue/all', 'client'
        correct = "SUBSCRIBE\nid:0\ndestination:%s\nack:%s\n\n\x00\n" % (dest, ack)
        self.assertEquals(stomper.subscribe(dest, 0, ack), correct)

        dest, ack = '/queue/all', 'auto'
        correct = "SUBSCRIBE\nid:0\ndestination:%s\nack:%s\n\n\x00\n" % (dest, ack)
        self.assertEquals(stomper.subscribe(dest, 0, ack), correct)

        correct = "SUBSCRIBE\nid:0\ndestination:%s\nack:%s\n\n\x00\n" % (dest, ack)
        self.assertEquals(stomper.subscribe(dest, 0), correct)

    def testConnect(self):
        username, password = 'bob', '123'
        correct = "CONNECT\naccept-version:1.1\nhost:localhost\nheart-beat:0,0\nlogin:%s\npasscode:%s\n\n\x00\n" % (username, password)
        self.assertEquals(stomper.connect(username, password, 'localhost'), correct)

    def testConnectWithHeartbeats(self):
        username, password = 'bob', '123'
        heartbeats = (1000, 1000)
        correct = "CONNECT\naccept-version:1.1\nhost:localhost\nheart-beat:1000,1000\nlogin:%s\npasscode:%s\n\n\x00\n" % (username, password)
        self.assertEquals(stomper.connect(username, password, 'localhost', heartbeats=heartbeats), correct)

    def testDisconnect(self):
        correct = "DISCONNECT\nreceipt:77\n\x00\n"
        self.assertEquals(stomper.disconnect(77), correct)

    def testSend(self):
        dest, transactionid, msg = '/queue/myplace', '', '123 456 789'
        correct = "SEND\ndestination:%s\ncontent-type:text/plain\n\n%s\x00\n" % (dest, msg)
        result = stomper.send(dest, msg, transactionid)

        self.assertEquals(result, correct)

        dest, transactionid, msg = '/queue/myplace', '987', '123 456 789'
        correct = "SEND\ndestination:%s\ncontent-type:text/plain\ntransaction:%s\n\n%s\x00\n" % (dest, transactionid, msg)
        self.assertEquals(stomper.send(dest, msg, transactionid), correct)

if __name__ == "__main__":
    unittest.main()
