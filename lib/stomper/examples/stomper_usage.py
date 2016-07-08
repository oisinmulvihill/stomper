"""
This is an example of generating messages, handling response 
messages and anything else I can think of demonstrating.

(c) Oisin Mulvihill, 2007-07-28.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
from __future__ import print_function
import pprint

import stomper


responder = stomper.Engine()

# Generate the connect command to tell the server about us:
msg = stomper.connect('bob','1234')
print("msg:\n%s\n" % pprint.pformat(msg))

#>>> 'CONNECT\nlogin:bob\npasscode:1234\n\n\x00\n'

# Send the message to the server and you'll get a response like:
#
server_response = """CONNECTED
session:ID:snorky.local-49191-1185461799654-3:18

\x00
"""


# We can react to this using the state machine to generate a response.
#
# The state machine can handle the raw message:
response = responder.react(server_response)

# or we could unpack the message into a dict and use it:
#
pprint.pprint(stomper.unpack_frame(response))

resp = responder.react(stomper.unpack_frame(response))

# The engine will store the session id from the CONNECTED
# response. It doesn't generate a message response. It
# just returns an empty string.


# After a successful connect you might want to subscribe
# for messages from a destination and tell the server you'll
# acknowledge all messages.
#
DESTINATION='/queue/inbox'
sub = stomper.subscribe(DESTINATION, ack='client')

# Send the message to the server...
#


# At some point in the future you'll get messages
# from the server. An example message might be:
#
server_msg = """MESSAGE
destination: /queue/a
message-id: some-message-id

hello queue a

\x00
"""

# We need to acknowledge this so we can pass this message 
# into the engine, and by default it will generate and
# ACK message:

response = responder.react(server_msg)
print("response:\n%s\n" % pprint.pformat(response))

#>>> 'ACK\nmessage-id: some-message-id\n\n\x00\n'



# We could over ride the default engine and do more customer
# reaction to receiving messages. For example:

class Pong(stomper.Engine):
    
    def ack(self, msg):
        """Override this and do some customer message handler.
        """
        print("Got a message:\n%s\n" % msg['body'])
        
        # do something with the message...
        
        # Generate the ack or not if you subscribed with ack='auto'
        return super(Pong, self).ack(msg)
        

responder2 = Pong()
response = responder2.react(server_msg)
print("response:\n%s\n" % pprint.pformat(response))
#>>> 'ACK\nmessage-id: some-message-id\n\n\x00\n'


# We might want to send a message at some point. We could do this
# in two ways

# 1. using the the function for send()
send_message = stomper.send(DESTINATION, 'hello there') 
print("1. send_message:\n%s\n" % pprint.pformat(send_message))

#>>> 'SEND\ndestination: /queue/inbox\n\nhello there\x00\n'


# 2. using the frame class to add extra custom headers:
msg = stomper.Frame()
msg.cmd = 'SEND'
msg.headers = {'destination':'/queue/a','custom-header':'1234'}
msg.body = "hello queue a"
print("2. send_message:\n%s\n" % pprint.pformat(msg.pack()))

#>>> 'SEND\ncustom-header:1234\ndestination:/queue/a\n\nhello queue a\n\n\x00\n'


# And thats pretty much it. There are other functions to send various 
# messages such as UNSUBSCRIBE, BEGIN, etc. Check out the stomper code
# for further details.
#


