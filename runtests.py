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


# Set up logging so we don't get any logger not found messages:
import stomper
#stomper.utils.log_init(logging.DEBUG)
stomper.utils.log_init(logging.CRITICAL)


class MyTestCollector(nose.LazySuite):
    """My test collector to run test from a specific list of dirs rather then just one or through discovery.
    """
    testLocations = []

    def __init__(self, conf, loader=None):
        self.locatedTests = []
        self.loader = nose.TestLoader(conf)

        # Recover tests from the various directories:
        for location in self.testLocations:
            self.locatedTests.extend(self.loader.loadTestsFromDir(location))

    def loadtests(self):
        for test in self.locatedTests:
            yield test

    def __repr__(self):
        return "collector for %s" % self.locatedTests
    __str__ = __repr__

# Use my collector only on the directries I want:
MyTestCollector.testLocations = test_paths
result = nose.core.TestProgram(defaultTest=MyTestCollector).success
nose.result.end_capture()

