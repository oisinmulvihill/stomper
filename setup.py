"""
Stomper distutils file.

(c) Oisin Mulvihill
2007-07-26

"""
import sys
from setuptools import setup, find_packages

sys.path.insert(0,'lib')
import stomper

Name='stomper'
#ProjecUrl="http://www.sourceweaver.com/autoconnect"
Version='0.1.0'
Author='Oisin Mulvihill'
AuthorEmail='oisin dot mulvihill at gmail com'
Maintainer=' Oisin Mulvihill'
Summary='This is a transport neutral client implementation of the STOMP protocol.'
License='http://www.apache.org/licenses/LICENSE-2.0'
ShortDescription="This is a transport neutral client implementation of the STOMP protocol."
Description=stomper.__doc__

TestSuite = 'stomper.tests'

ProjectScripts = [
#    '',
]

PackageData = {
    # If any package contains *.txt or *.rst files, include them:
    '': ['*.txt', '*.rst', 'ini'],
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
