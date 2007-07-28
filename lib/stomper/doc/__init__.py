"""
This is used in the setup.py to read in the docs and assign it to
the description in the setup.py.

(c) Oisin Mulvihill, 2007-07-28.
License: http://www.apache.org/licenses/LICENSE-2.0

"""
import os

doc_dir = os.path.dirname(__file__)

documentation = os.path.join(doc_dir, "stomper.stx")
