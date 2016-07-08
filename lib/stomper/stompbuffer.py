"""
StompBuffer is an optional utility class accompanying Stomper.

Ricky Iacovou, 2008-03-27. 

License: http://www.apache.org/licenses/LICENSE-2.0

"""
from builtins import object

import re
import stomper

# regexp to check that the buffer starts with a command.
command_re = re.compile ( '^(.*?)\n' )

# regexp to remove everything up to and including the first
# instance of '\x00\n' (used in resynching the buffer).
sync_re = re.compile ( '^.*?\x00\n' )

# regexp to determine the content length. The buffer should always start
# with a command followed by the headers, so the content-length header will
# always be preceded by a newline.
content_length_re = re.compile ( '\ncontent-length\s*:\s*(\d+)\s*\n' )

# Separator between the header and the body.
len_sep = len ( '\n\n' )
# Footer after the message body.
len_footer = len ( '\x00\n' )

class StompBuffer ( object ):
    """
    I can be used to deal with partial frames if your transport does
    not guarantee complete frames. I maintain an internal buffer of
    received bytes and offer a way of pulling off the first complete
    message off the buffer.
    """

    def __init__ ( self ):
        self.buffer = ''


    def bufferLen ( self ):
        """
        I return the length of the buffer, in bytes.
        """
        return len ( self.buffer )
    
    
    def bufferIsEmpty ( self ):
        """
        I return True if the buffer contains zero bytes, False otherwise.
        """
        return self.bufferLen() == 0
        

    def appendData ( self, data ):
        """
        I should be called by a transport that receives a raw
        sequence of bytes that may or may not contain a complete
        message. I return
        """
        # log.msg ( "Received [%s] bytes in dataReceived()" % ( len ( data ), ) )
        # import pprint
        # pprint.pprint ( data )
        self.buffer += data


    def getOneMessage ( self ):
        """
        I pull one complete message off the buffer and return it decoded
        as a dict. If there is no complete message in the buffer, I
        return None.

        Note that the buffer can contain more than once message. You
        should therefore call me in a loop until I return None.
        """
        ( mbytes, hbytes ) = self._findMessageBytes ( self.buffer )
        if not mbytes:
            return None
        
        msgdata = self.buffer[:mbytes]
        self.buffer = self.buffer[mbytes:]
        hdata = msgdata[:hbytes]
        elems = hdata.split ( '\n' )
        cmd     = elems.pop ( 0 )
        headers = {}
        # We can't use a simple split because the value can legally contain
        # colon characters (for example, the session returned by ActiveMQ).
        for e in elems:
            try:
                i = e.find ( ':' )
            except ValueError:
                continue
            k = e[:i].strip()
            v = e[i+1:].strip()
            headers [ k ] = v

        # hbytes points to the start of the '\n\n' at the end of the header,
        # so 2 bytes beyond this is the start of the body. The body EXCLUDES
        # the final two bytes, which are '\x00\n'. Note that these 2 bytes
        # are UNRELATED to the 2-byte '\n\n' that Frame.pack() used to insert
        # into the data stream.
        body = msgdata[hbytes+2:-2]
        msg = { 'cmd'     : cmd,
                'headers' : headers,
                'body'    : body,
                }
        return msg


    def _findMessageBytes ( self, data ):
        """
        I examine the data passed to me and return a 2-tuple of the form:
        
          ( message_length, header_length )
          
        where message_length is the length in bytes of the first complete
        message, if it contains at least one message, or 0 if it
        contains no message.
        
        If message_length is non-zero, header_length contains the length in
        bytes of the header. If message_length is zero, header_length should
        be ignored.

        You should probably not call me directly. Call getOneMessage instead.
        """

        # Sanity check. See the docstring for the method to see what it
        # does an why we need it.
        self.syncBuffer()
        
        # If the string '\n\n' does not exist, we don't even have the complete
        # header yet and we MUST exit.
        try:
            i = data.index ( '\n\n' )
        except ValueError:
            return ( 0, 0 )
        # If the string '\n\n' exists, then we have the entire header and can
        # check for the content-length header. If it exists, we can check
        # the length of the buffer for the number of bytes, else we check for
        # the existence of a null byte.

        # Pull out the header before we perform the regexp search. This
        # prevents us from matching (possibly malicious) strings in the
        # body.
        _hdr = self.buffer[:i]
        match = content_length_re.search ( _hdr )
        if match:
            # There was a content-length header, so read out the value.
            content_length = int ( match.groups()[0] )

            # THIS IS NO LONGER THE CASE IF WE REMOVE THE '\n\n' in
            # Frame.pack()
            
            # This is the content length of the body up until the null
            # byte, not the entire message. Note that this INCLUDES the 2
            # '\n\n' bytes inserted by the STOMP encoder after the body
            # (see the calculation of content_length in
            # StompEngine.callRemote()), so we only need to add 2 final bytes
            # for the footer.
            #
            #The message looks like:
            #
            #   <header>\n\n<body>\n\n\x00\n
            #           ^         ^^^^
            #          (i)         included in content_length!
            #
            # We have the location of the end of the header (i), so we
            # need to ensure that the message contains at least:
            #
            #     i + len ( '\n\n' ) + content_length + len ( '\x00\n' )
            #
            # Note that i is also the count of bytes in the header, because
            # of the fact that str.index() returns a 0-indexed value.
            req_len = i + len_sep + content_length + len_footer
            # log.msg ( "We have [%s] bytes and need [%s] bytes" %
            #           ( len ( data ), req_len, ) )
            if len ( data ) < req_len:
                # We don't have enough bytes in the buffer.
                return ( 0, 0 )
            else:
                # We have enough bytes in the buffer
                return ( req_len, i )
        else:
            # There was no content-length header, so just look for the
            # message terminator ('\x00\n' ).
            try:
                j = data.index ( '\x00\n' )
            except ValueError:
                return ( 0, 0 )
            # j points to the 0-indexed location of the null byte. However,
            # we need to add 1 (to turn it into a byte count) and 1 to take
            # account of the final '\n' character after the null byte.
            return ( j + 2, i )


    def syncBuffer( self ):
        """
        I detect and correct corruption in the buffer.
        
        Corruption in the buffer is defined as the following conditions
        both being true:
        
            1. The buffer contains at least one newline;
            2. The text until the first newline is not a STOMP command.
        
        In this case, we heuristically try to flush bits of the buffer until
        one of the following conditions becomes true:
        
            1. the buffer starts with a STOMP command;
            2. the buffer does not contain a newline.
            3. the buffer is empty;

        If the buffer is deemed corrupt, the first step is to flush the buffer
        up to and including the first occurrence of the string '\x00\n', which
        is likely to be a frame boundary.

        Note that this is not guaranteed to be a frame boundary, as a binary
        payload could contain the string '\x00\n'. That condition would get
        handled on the next loop iteration.
        
        If the string '\x00\n' does not occur, the entire buffer is cleared.
        An earlier version progressively removed strings until the next newline,
        but this gets complicated because the body could contain strings that
        look like STOMP commands.
        
        Note that we do not check "partial" strings to see if they *could*
        match a command; that would be too resource-intensive. In other words,
        a buffer containing the string 'BUNK' with no newline is clearly
        corrupt, but we sit and wait until the buffer contains a newline before
        attempting to see if it's a STOMP command.
        """
        while True:
            if not self.buffer:
                # Buffer is empty; no need to do anything.
                break
            m = command_re.match ( self.buffer )
            if m is None:
                # Buffer doesn't even contain a single newline, so we can't
                # determine whether it's corrupt or not. Assume it's OK.
                break
            cmd = m.groups()[0]
            if cmd in stomper.VALID_COMMANDS:
                # Good: the buffer starts with a command.
                break
            else:
                # Bad: the buffer starts with bunk, so strip it out. We first
                # try to strip to the first occurrence of '\x00\n', which
                # is likely to be a frame boundary, but if this fails, we
                # strip until the first newline.
                ( self.buffer, nsubs ) = sync_re.subn ( '', self.buffer )

                if nsubs:
                    # Good: we managed to strip something out, so restart the
                    # loop to see if things look better.
                    continue
                else:
                    # Bad: we failed to strip anything out, so kill the
                    # entire buffer. Since this resets the buffer to a
                    # known good state, we can break out of the loop.
                    self.buffer = ''
                    break

