# ! important
# see https://stackoverflow.com/a/27868004/1497139
from setuptools import setup

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyjanusgraph',
    version='0.0.1a2',

    packages=['tp',],
    author='Wolfgang Fahl',
    maintainer='Wolfgang Fahl',
    url='https://github.com/BITPlan/pyjanusgraph',
    license='Apache License',
    description='Python janusgraph utility library',
    long_description=long_description,
    long_description_content_type='text/markdown'
)
