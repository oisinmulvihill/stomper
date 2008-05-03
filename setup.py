"""
Stomper distutils file.

(c) Oisin Mulvihill
2007-07-26

"""
from setuptools import setup, find_packages


Name='stomper'
ProjecUrl="http://code.google.com/p/stomper"
Version='0.2.2' # alpha release
Author='Oisin Mulvihill'
AuthorEmail='oisin dot mulvihill at gmail com'
Maintainer=' Oisin Mulvihill'
Summary='This is a transport neutral client implementation of the STOMP protocol.'
License='http://www.apache.org/licenses/LICENSE-2.0'
ShortDescription="This is a transport neutral client implementation of the STOMP protocol."
Classifiers=[
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python",
]

# Recover the ReStructuredText docs:
fd = file("lib/stomper/doc/stomper.stx")
Description=fd.read()
fd.close()

TestSuite = 'stomper.tests'

# stop any logger not found messages  if tests are run.
#stomper.utils.log_init(logging.CRITICAL)


ProjectScripts = [
#    '',
]

PackageData = {
    # If any package contains *.txt or *.rst files, include them:
    'stomper': ['doc/*.stx',],
}


needed = [
    'uuid>=1.2',
]

setup(
#    url=ProjecUrl,
    name=Name,
    version=Version,
    author=Author,
    author_email=AuthorEmail,
    description=ShortDescription,
    long_description=Description,
    url=ProjecUrl,
    license=License,
    classifiers=Classifiers,
    install_requires=needed,
    test_suite=TestSuite,
    scripts=ProjectScripts,
    packages=find_packages('lib'),
    package_data=PackageData,
    package_dir = {'': 'lib'},
)


