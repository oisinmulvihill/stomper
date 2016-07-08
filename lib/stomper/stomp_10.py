"""
This is a python client implementation of the STOMP protocol.

It aims to be transport layer neutral. This module provides functions to
create and parse STOMP messages in a programmatic fashion.

The examples package contains two examples using twisted as the transport
framework. Other frameworks can be used and I may add other examples as
time goes on.

The STOMP protocol specification maybe found here:

 * http://stomp.codehaus.org/Protocol

I've looked at the stomp client by Jason R. Briggs and have based the message
generation on how his client does it. The client can be found at the follow
address however it isn't a dependancy.

 * http://www.briggs.net.nz/log/projects/stomppy

In testing this library I run against ActiveMQ project. The server runs
in java, however its fairly standalone and easy to set up. The projects
page is here:

 * http://activemq.apache.org/


(c) Oisin Mulvihill, 2007-07-26.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
from __future__ import absolute_import
from builtins import object
import re
import uuid
import types
import logging


from . import utils
from . import stompbuffer

# This is used as a return from message responses functions.
# It is used more for readability more then anything or reason.
NO_RESPONSE_NEEDED = ''

# For backwards compatibility
NO_REPONSE_NEEDED = ''


# The version of the protocol we implement.
STOMP_VERSION = '1.0'

# Message terminator:
NULL = '\x00'

# STOMP Spec v1.0 valid commands:
VALID_COMMANDS = [
    'ABORT', 'ACK', 'BEGIN', 'COMMIT',
    'CONNECT', 'CONNECTED', 'DISCONNECT', 'MESSAGE',
    'SEND', 'SUBSCRIBE', 'UNSUBSCRIBE',
    'RECEIPT', 'ERROR',
]

try:
    stringTypes = (str, unicode)
except NameError:
    stringTypes = (str,)


def get_log():
    return logging.getLogger("stomper")


class FrameError(Exception):
    """Raise for problem with frame generation or parsing.
    """


class Frame(object):
    """This class is used to create or read STOMP message frames.

    The method pack() is used to create a STOMP message ready
    for transmission.

    The method unpack() is used to read a STOMP message into
    a frame instance. It uses the unpack_frame(...) function
    to do the initial parsing.

    The frame has three important member variables:

      * cmd
      * headers
      * body

    The 'cmd' is a property that represents the STOMP message
    command. When you assign this a check is done to make sure
    its one of the VALID_COMMANDS. If not then FrameError will
    be raised.

    The 'headers' is a dictionary which the user can added to
    if needed. There are no restrictions or checks imposed on
    what values are inserted.

    The 'body' is just a member variable that the body text
    is assigned to.

    """
    def __init__(self):
        """Setup the internal state."""
        self._cmd = ''
        self.body = ''
        self.headers = {}

    def getCmd(self):
        """Don't use _cmd directly!"""
        return self._cmd

    def setCmd(self, cmd):
        """Check the cmd is valid, FrameError will be raised if its not."""
        cmd = cmd.upper()
        if cmd not in VALID_COMMANDS:
            raise FrameError("The cmd '%s' is not valid! It must be one of '%s' (STOMP v%s)." % (
                cmd, VALID_COMMANDS, STOMP_VERSION)
            )
        else:
            self._cmd = cmd

    cmd = property(getCmd, setCmd)

    def pack(self):
        """Called to create a STOMP message from the internal values.
        """
        headers = ''.join(
            ['%s:%s\n' % (f, v) for f, v in sorted(self.headers.items())]
        )
        stomp_message = "%s\n%s\n%s%s\n" % (self._cmd, headers, self.body, NULL)

#        import pprint
#        print "stomp_message: ", pprint.pprint(stomp_message)

        return stomp_message


    def unpack(self, message):
        """Called to extract a STOMP message into this instance.

        message:
            This is a text string representing a valid
            STOMP (v1.0) message.

        This method uses unpack_frame(...) to extract the
        information, before it is assigned internally.

        retuned:
            The result of the unpack_frame(...) call.

        """
        if not message:
            raise FrameError("Unpack error! The given message isn't valid '%s'!" % message)

        msg = unpack_frame(message)

        self.cmd = msg['cmd']
        self.headers = msg['headers']

        # Assign directly as the message will have the null
        # character in the message already.
        self.body = msg['body']

        return msg


def unpack_frame(message):
    """Called to unpack a STOMP message into a dictionary.

    returned = {
        # STOMP Command:
        'cmd' : '...',

        # Headers e.g.
        'headers' : {
            'destination' : 'xyz',
            'message-id' : 'some event',
            :
            etc,
        }

        # Body:
        'body' : '...1234...\x00',
    }

    """
    body = []
    returned = dict(cmd='', headers={}, body='')

    breakdown = message.split('\n')

    # Get the message command:
    returned['cmd'] = breakdown[0]
    breakdown = breakdown[1:]

    def headD(field):
        # find the first ':' everything to the left of this is a
        # header, everything to the right is data:
        index = field.find(':')
        if index:
            header = field[:index].strip()
            data = field[index+1:].strip()
#            print "header '%s' data '%s'" % (header, data)
            returned['headers'][header.strip()] = data.strip()

    def bodyD(field):
        field = field.strip()
        if field:
            body.append(field)

    # Recover the header fields and body data
    handler = headD
    for field in breakdown:
#        print "field:", field
        if field.strip() == '':
            # End of headers, it body data next.
            handler = bodyD
            continue

        handler(field)

    # Stich the body data together:
#    print "1. body: ", body
    body = "".join(body)
    returned['body'] = body.replace('\x00', '')

#    print "2. body: <%s>" % returned['body']

    return returned


def abort(transactionid):
    """STOMP abort transaction command.

    Rollback whatever actions in this transaction.

    transactionid:
        This is the id that all actions in this transaction.

    """
    return "ABORT\ntransaction: %s\n\n\x00\n" % transactionid


def ack(messageid, transactionid=None):
    """STOMP acknowledge command.

    Acknowledge receipt of a specific message from the server.

    messageid:
        This is the id of the message we are acknowledging,
        what else could it be? ;)

    transactionid:
        This is the id that all actions in this transaction
        will have. If this is not given then a random UUID
        will be generated for this.

    """
    header = 'message-id: %s' % messageid

    if transactionid:
        header = 'message-id: %s\ntransaction: %s' % (messageid, transactionid)

    return "ACK\n%s\n\n\x00\n" % header


def begin(transactionid=None):
    """STOMP begin command.

    Start a transaction...

    transactionid:
        This is the id that all actions in this transaction
        will have. If this is not given then a random UUID
        will be generated for this.

    """
    if not transactionid:
        # Generate a random UUID:
        transactionid = uuid.uuid4()

    return "BEGIN\ntransaction: %s\n\n\x00\n" % transactionid


def commit(transactionid):
    """STOMP commit command.

    Do whatever is required to make the series of actions
    permanent for this transactionid.

    transactionid:
        This is the id that all actions in this transaction.

    """
    return "COMMIT\ntransaction: %s\n\n\x00\n" % transactionid


def connect(username, password):
    """STOMP connect command.

    username, password:
        These are the needed auth details to connect to the
        message server.

    After sending this we will receive a CONNECTED
    message which will contain our session id.

    """
    return "CONNECT\nlogin:%s\npasscode:%s\n\n\x00\n" % (username, password)


def disconnect():
    """STOMP disconnect command.

    Tell the server we finished and we'll be closing the
    socket soon.

    """
    return "DISCONNECT\n\n\x00\n"


def send(dest, msg, transactionid=None):
    """STOMP send command.

    dest:
        This is the channel we wish to subscribe to

    msg:
        This is the message body to be sent.

    transactionid:
        This is an optional field and is not needed
        by default.

    """
    transheader = ''

    if transactionid:
        transheader = 'transaction: %s\n' % transactionid

    return "SEND\ndestination: %s\n%s\n%s\x00\n" % (dest, transheader, msg)


def subscribe(dest, ack='auto'):
    """STOMP subscribe command.

    dest:
        This is the channel we wish to subscribe to

    ack: 'auto' | 'client'
        If the ack is set to client, then messages received will
        have to have an acknowledge as a reply. Otherwise the server
        will assume delivery failure.

    """
    return "SUBSCRIBE\ndestination: %s\nack: %s\n\n\x00\n" % (dest, ack)


def unsubscribe(dest):
    """STOMP unsubscribe command.

    dest:
        This is the channel we wish to subscribe to

    Tell the server we no longer wish to receive any
    further messages for the given subscription.

    """
    return "UNSUBSCRIBE\ndestination:%s\n\n\x00\n" % dest


class Engine(object):
    """This is a simple state machine to return a response to received
    message if needed.

    """
    def __init__(self, testing=False):
        self.testing = testing

        self.log = logging.getLogger("stomper.Engine")

        self.sessionId = ''

        # Entry Format:
        #
        #    COMMAND : Handler_Function
        #
        self.states = {
            'CONNECTED' : self.connected,
            'MESSAGE' : self.ack,
            'ERROR' : self.error,
            'RECEIPT' : self.receipt,
        }


    def react(self, msg):
        """Called to provide a response to a message if needed.

        msg:
            This is a dictionary as returned by unpack_frame(...)
            or it can be a straight STOMP message. This function
            will attempt to determine which an deal with it.

        returned:
            A message to return or an empty string.

        """
        returned = ""

        # If its not a string assume its a dict.
        mtype = type(msg)
        if mtype in stringTypes:
            msg = unpack_frame(msg)
        elif mtype == dict:
            pass
        else:
            raise FrameError("Unknown message type '%s', I don't know what to do with this!" % mtype)

        if msg['cmd'] in self.states:
#            print("reacting to message - %s" % msg['cmd'])
            returned = self.states[msg['cmd']](msg)

        return returned


    def connected(self, msg):
        """No response is needed to a connected frame.

        This method stores the session id as the
        member sessionId for later use.

        returned:
            NO_RESPONSE_NEEDED

        """
        self.sessionId = msg['headers']['session']
        #print "connected: session id '%s'." % self.sessionId

        return NO_RESPONSE_NEEDED


    def ack(self, msg):
        """Called when a MESSAGE has been received.

        Override this method to handle received messages.

        This function will generate an acknowledge message
        for the given message and transaction (if present).

        """
        message_id = msg['headers']['message-id']

        transaction_id = None
        if 'transaction-id' in msg['headers']:
            transaction_id = msg['headers']['transaction-id']

#        print "acknowledging message id <%s>." % message_id

        return ack(message_id, transaction_id)


    def error(self, msg):
        """Called to handle an error message received from the server.

        This method just logs the error message

        returned:
            NO_RESPONSE_NEEDED

        """
        body = msg['body'].replace(NULL, '')

        brief_msg = ""
        if 'message' in msg['headers']:
            brief_msg = msg['headers']['message']

        self.log.error("Received server error - message%s\n\n%s" % (brief_msg, body))

        returned = NO_RESPONSE_NEEDED
        if self.testing:
            returned = 'error'

        return returned


    def receipt(self, msg):
        """Called to handle a receipt message received from the server.

        This method just logs the receipt message

        returned:
            NO_RESPONSE_NEEDED

        """
        body = msg['body'].replace(NULL, '')

        brief_msg = ""
        if 'receipt-id' in msg['headers']:
            brief_msg = msg['headers']['receipt-id']

        self.log.info("Received server receipt message - receipt-id:%s\n\n%s" % (brief_msg, body))

        returned = NO_RESPONSE_NEEDED
        if self.testing:
            returned = 'receipt'

        return returned

