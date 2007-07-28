"""
Stomper distutils file.

(c) Oisin Mulvihill
2007-07-26

"""
import sys
import logging
from setuptools import setup, find_packages

sys.path.insert(0,'lib')
import stomper

Name='stomper'
#ProjecUrl="http://www.sourceweaver.com/stomper"
Version='0.2.0'
Author='Oisin Mulvihill'
AuthorEmail='oisin dot mulvihill at gmail com'
Maintainer=' Oisin Mulvihill'
Summary='This is a transport neutral client implementation of the STOMP protocol.'
License='http://www.apache.org/licenses/LICENSE-2.0'
ShortDescription="This is a transport neutral client implementation of the STOMP protocol."

# Recover the ReStructuredText docs:
fd = file(stomper.doc.documentation)
Description=fd.read()
fd.close()

TestSuite = 'stomper.tests'

# stop any logger not found messages  if tests are run.
stomper.utils.log_init(logging.CRITICAL)


ProjectScripts = [
#    '',
]

PackageData = {
    # If any package contains *.txt or *.rst files, include them:
    'stomper': ['doc/*.stx',],
}

setup(
#    url=ProjecUrl,
    name=Name,
    version=Version,
    author=Author,
    author_email=AuthorEmail,
    description=ShortDescription,
    long_description=Description,
    license=License,
    test_suite=TestSuite,
    scripts=ProjectScripts,
    packages=find_packages('lib'),
    package_data=PackageData,
    package_dir = {'': 'lib'},
)
