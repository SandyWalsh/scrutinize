import os
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='scrutinize',
    version='0.1.0',
    author='Sandy Walsh',
    author_email='scrutinize@darksecretsoftware.com',
    description=("Monkeypatching library for python profiling and "
                 "measurements. Based on the work of Matt Dietz's Tach."),
    license='Apache License (2.0)',
    keywords='metrics, statsd, profile, timing',
    packages=find_packages(exclude=['test']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6'
    ],
    url='https://github.com/sandywalsh/scrutinize',
    scripts=['bin/scrutinize'],
    long_description=read('README.md'),
    install_requires=[''],
    data_files=[('', ['conf/sample.json'])],
    zip_safe=False
)
