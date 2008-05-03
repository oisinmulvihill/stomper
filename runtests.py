#!/usr/bin/env python
#
# Use nosetests to run the acceptance tests for this project.
#
# This script sets up the paths to find packages (see package_paths)
# and limits the test discovery to only the listed set of locations
# (see test_paths).
#
# Oisin Mulvihill
# 2007-07-28
#
import os
import sys
import nose
import logging


# These are where to find the various app and webapp
# packages, along with any other thirdparty stuff.
package_paths = [
    "./lib",
]
sys.path.extend(package_paths)


# Only bother looking for tests in these locations:
# (Note: these need to be absolute paths)
current = os.path.abspath(os.path.curdir)
test_paths = [
    current + "/lib/stomper/tests",
]
env = os.environ
env['NOSE_WHERE'] = ' '.join(test_paths)


# Set up logging so we don't get any logger not found messages:
import stomper
#stomper.utils.log_init(logging.DEBUG)
stomper.utils.log_init(logging.CRITICAL)


result = nose.core.TestProgram(env=env).success
nose.result.end_capture()


