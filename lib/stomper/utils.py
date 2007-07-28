"""
This module contains various utility functions used in various locations.

(c) Oisin Mulvihill, 2007-07-28.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
import logging


def log_init(level):
    """Set up a logger that catches all channels and logs it to stdout.
    
    This is used to set up logging when testing.
    
    """
    log = logging.getLogger()
    hdlr = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(level)
