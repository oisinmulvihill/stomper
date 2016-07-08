######################################################################
# Unit tests for StompBuffer
######################################################################

import unittest
import types

import stomper
from stomper.stompbuffer import StompBuffer

CMD  = 'SEND'
DEST = '/queue/a'
BODY = 'This is the body text'
BINBODY = '\x00\x01\x03\x04\x05\x06'

def makeTextMessage ( body = BODY, cmd = CMD ):
    msg = stomper.Frame()
    msg.cmd = cmd
    msg.headers = {'destination':DEST}
    msg.body = body
    return msg.pack()

def makeBinaryMessage ( body = BINBODY, cmd = CMD ):
    msg = stomper.Frame()
    msg.cmd = cmd
    msg.headers = {'destination':DEST, 'content-length':len(body)}
    msg.body = body
    return msg.pack()

def messageIsGood ( msg, body = BODY, cmd = CMD ):
    if msg is None:
        return False
    if type ( msg ) != dict:
        return False
    if msg [ 'cmd' ] != cmd:
        return False
    try:
        dest = msg [ 'headers' ][ 'destination' ]
    except KeyError:
        return False
    if dest != DEST:
        return False
    if msg [ 'body' ] != body:
        return False
    return True


class StompBufferTestCase ( unittest.TestCase ):

    def setUp ( self ):
        self.sb = StompBuffer()


    # We do this so often we put it into a separate method.
    def putAndGetText ( self ):
        msg = makeTextMessage()
        self.sb.appendData ( msg )
        return self.sb.getOneMessage()


    def putAndGetBinary ( self ):
        msg = makeBinaryMessage()
        self.sb.appendData ( msg )
        return self.sb.getOneMessage()


    def test001_testBufferAccretionText ( self ):
        """
        Test to see that the buffer accumulates text
        messages with no additional padding.
        """
        msg1 = makeTextMessage ( 'blah1' )
        msg2 = makeTextMessage ( 'blah2' )
        msg3 = makeTextMessage ( 'blah3' )
        self.sb.appendData ( msg1 )
        self.sb.appendData ( msg2 )
        self.sb.appendData ( msg3 )
        expect = len ( msg1 ) + len ( msg2 ) + len ( msg3 )
        self.failUnless ( self.sb.bufferLen() == expect )


    def test002_testBufferAccretionBinary ( self ):
        """
        Test to see that the buffer accumulates binary
        messages with no additional padding.
        """
        msg1 = makeBinaryMessage ( 'blah1' )
        msg2 = makeBinaryMessage ( 'blah2' )
        msg3 = makeBinaryMessage ( 'blah3' )
        self.sb.appendData ( msg1 )
        self.sb.appendData ( msg2 )
        self.sb.appendData ( msg3 )
        expect = len ( msg1 ) + len ( msg2 ) + len ( msg3 )
        self.failUnless ( self.sb.bufferLen() == expect )


    def test003_oneCompleteTextMessage ( self ):
        """
        Put a complete text message into the buffer, read it out again, and
        verify the decoded message. There are actually lots of little tests,
        but they're all part of the process of verifying the decoded message.

        Note that this test will FAIL if Frame.pack() inserts the additional
        '\n\n' bytes.
        """
        msg = self.putAndGetText()
        self.failUnless ( messageIsGood )


    def test004_oneCompleteBinaryMessage ( self ):
        """
        Put a complete binary message into the buffer, read it out again, and
        verify the decoded message.

        Note that this test will FAIL if Frame.pack() inserts the additional
        '\n\n' bytes.
        """
        msg = self.putAndGetBinary()
        self.failUnless ( messageIsGood ( msg, BINBODY ) )


    def test005_emptyBufferText ( self ):
        """
        Put a complete text message into the buffer, read it out again, and
        verify that there is nothing left in the buffer.
        """
        # Verify that there are no more messages in the buffer.
        msg1 = self.putAndGetText()
        msg2 = self.sb.getOneMessage()
        self.failUnless ( msg2 is None )
        # Verify that in fact the buffer is empty.
        self.failUnless ( self.sb.bufferIsEmpty() )


    def test006_emptyBufferBinary ( self ):
        """
        Put a complete binary message into the buffer, read it out again, and
        verify that there is nothing left in the buffer.
        """
        # Verify that there are no more messages in the buffer.
        msg1 = self.putAndGetBinary()
        msg2 = self.sb.getOneMessage()
        self.failUnless ( msg2 is None )
        # Verify that in fact the buffer is empty.
        self.failUnless ( self.sb.bufferIsEmpty() )


    def test007_messageFragmentsText ( self ):
        """
        Create a text message and check that the we can't read it out until
        we've fed all parts into the buffer
        """
        msg = makeTextMessage()
        fragment1 = msg [:20]
        fragment2 = msg [20:]
        self.sb.appendData ( fragment1 )
        m = self.sb.getOneMessage()
        self.failUnless ( m is None )
        self.sb.appendData ( fragment2 )
        m = self.sb.getOneMessage()
        self.failIf ( m is None )
        self.failUnless ( self.sb.bufferIsEmpty() )


    def test008_messageFragmentsBinary ( self ):
        """
        Create a binary message and check that the we can't read it out until
        we've fed all parts into the buffer
        """
        msg = makeBinaryMessage()
        fragment1 = msg [:20]
        fragment2 = msg [20:]
        self.sb.appendData ( fragment1 )
        m = self.sb.getOneMessage()
        self.failUnless ( m is None )
        self.sb.appendData ( fragment2 )
        m = self.sb.getOneMessage()
        self.failIf ( m is None )
        self.failUnless ( self.sb.bufferIsEmpty() )


    def test009_confusingMessage ( self ):
        """
        Create a confusing message and ensure that the decoder doesn't get
        tripped up.
        """
        # Throw in fake commands, headers, nulls, newlines, everything.
        body = 'SUBSCRIBE\ncontent-length:27\n\x00\ndestination:/queue/confusion\n\n\x00\n'
        msg = makeBinaryMessage ( body )
        self.sb.appendData ( msg )
        m = self.sb.getOneMessage()
        # Ensure the headers weren't mangled
        self.failUnless ( m [ 'cmd' ] == CMD )
        self.failUnless ( m [ 'headers' ] [ 'destination' ] == DEST )
        # Ensure the body wasn't mangled.
        self.failUnless ( m [ 'body' ] == body )
        # But ensure that there isn't object identity going on behind the
        # scenes.
        self.failIf ( m [ 'body' ] is body )
        # Ensure the message was consumed in its entirety.
        self.failUnless ( self.sb.bufferIsEmpty() )


    def test010_syncBufferNoClobber ( self ):
        """
        Test that syncBuffer doesn't clobber the buffer if it doesn't
        contain a newline.
        """
        self.sb.buffer = 'BLAHBLAH'
        self.sb.syncBuffer()
        self.failUnless ( self.sb.buffer == "BLAHBLAH" )

        
    def test011_syncBufferClobberEverything ( self ):
        """
        Put bunk into the buffer and ensure that it gets detected and removed.
        In this case, the entire buffer should be killed.
        """
        self.sb.buffer = 'rubbish\nmorerubbish'
        self.sb.syncBuffer()
        self.failUnless ( self.sb.bufferIsEmpty() )

        
    def test012_syncBufferClobberRubbish ( self ):
        """
        Put bunk into the buffer and ensure that it gets detected and removed.
        In this case, only the start of the buffer should be killed, and
        the remainder should be left alone as it could be a partial command.
        """
        self.sb.buffer = 'rubbish\x00\nREMAINDER'
        self.sb.syncBuffer()
        self.failUnless ( self.sb.buffer == "REMAINDER" )

        
    def test013_syncBufferClobberEverythingTwice ( self ):
        """
        Put bunk into the buffer and ensure that it gets detected and removed.
        In this case, the entire buffer should be clobbered as once we have
        removed the corrupt start of the data, it should become obvious that
        the rest of the buffer is corrupt too.
        """
        self.sb.buffer = 'rubbish\x00\nNOTACOMMAND\n'
        self.sb.syncBuffer()
        self.failUnless ( self.sb.bufferIsEmpty() )

        
    def test014_syncBufferGetGoodMessage ( self ):
        """
        Put bunk into the buffer, followed by a real message and ensure that
        the bunk gets detected and removed and the message gets retrieved.
        """
        msg = makeTextMessage()
        self.sb.buffer = 'rubbish\x00\n%s' % ( msg, )
        self.sb.syncBuffer()
        m = self.sb.getOneMessage()
        self.failUnless ( messageIsGood ( m ) )


    def test015_syncBufferClobberGoodMessage ( self ):
        """
        Put bunk into the buffer, followed by a real message NOT
        separated by '\x00\n' and ensure that the whole buffer gets
        deleted.
        """
        msg = makeTextMessage()
        self.sb.buffer = 'rubbish\n%s' % ( msg, )
        self.sb.syncBuffer()
        self.failUnless ( self.sb.bufferIsEmpty() )


    def test016_syncBufferHandleEmbeddedNulls ( self ):
        """
        Put bunk into the buffer including an embedded '\x00\n' string,
        followed by a real message, and ensure that all the junk gets deleted
        but the real message is kept.
        """
        msg = makeTextMessage()
        # The first null byte is embedded rubbish. The next null byte
        # should be treated as an end-of-frame delineator preceding the
        # real message.
        self.sb.buffer = 'rubbish\x00\nmorerubbish\x00\n%s' % ( msg, )
        self.sb.syncBuffer()
        m = self.sb.getOneMessage()
        self.failUnless ( messageIsGood ( m ) )

    def test017_testAllCommands ( self ):
        # Intentionally NOT using stomper.VALID_COMMANDS
        for cmd in [ 'SEND', 'SUBSCRIBE', 'UNSUBSCRIBE', 'BEGIN',
                     'COMMIT', 'ABORT', 'ACK', 'DISCONNECT',
                     'CONNECTED', 'MESSAGE', 'RECEIPT', 'ERROR' ]:
            msg = makeTextMessage ( body = BODY, cmd = cmd )
            self.sb.appendData ( msg )
            m = self.sb.getOneMessage()
            self.failUnless ( messageIsGood ( m, BODY, cmd ) )
            self.failUnless ( self.sb.bufferIsEmpty() )

        
if __name__ == "__main__":
    unittest.main() # run all tests
    
