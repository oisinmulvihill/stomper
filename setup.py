"""
Stomper distutils file.

(c) Oisin Mulvihill
2007-07-26

"""
import sys
from setuptools import setup, find_packages


Name = 'stomper'
ProjectUrl = "https://github.com/oisinmulvihill/stomper"
Version = '0.4.1'
Author = 'Oisin Mulvihill'
AuthorEmail = 'oisin dot mulvihill at gmail com'
Maintainer = 'Oisin Mulvihill'
Summary = (
    'This is a transport neutral client implementation '
    'of the STOMP protocol.'
)
License = 'http://www.apache.org/licenses/LICENSE-2.0'
ShortDescription = (
    "This is a transport neutral client implementation of the "
    "STOMP protocol."
)
Classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python",
]

# Recover the ReStructuredText docs:
Description = open("README.rst", "rb").read().decode("utf-8")

TestSuite = 'stomper.tests'

# stop any logger not found messages  if tests are run.
#stomper.utils.log_init(logging.CRITICAL)

ProjectScripts = []

PackageData = {
}


needed = ['future']
if sys.version_info < (2, 5):
    needed += [
        'uuid>=1.2',
    ]

setup(
    name=Name,
    version=Version,
    author=Author,
    author_email=AuthorEmail,
    description=ShortDescription,
    long_description=Description,
    url=ProjectUrl,
    license=License,
    classifiers=Classifiers,
    install_requires=needed,
    test_suite=TestSuite,
    scripts=ProjectScripts,
    packages=find_packages('lib'),
    package_data=PackageData,
    package_dir={'': 'lib'},
)
