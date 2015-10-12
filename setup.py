"""
This file is part of S

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os

from setuptools import setup
from setuptools import find_packages


name = 'storm'
version = '1.0.0'


def _read(filename):
    with open(filename) as r:
        return r.read()

def readme():
    return _read('README.rst')


def find_requires():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open('{0}/requirements.txt'.format(dir_path), 'r') as reqs:
        return reqs.readlines()

if __name__ == '__main__':
    setup(
        name=name,
        version=version,
        description='The library to easy build rest-full web applications based on asynchronous engines',
        keywords='web rest async',
        packages=find_packages(),
        zip_safe=False,
        install_requires=find_requires(),
        author="Bulat Gaifullin",
        author_email="gaifullinbf@gmail.com",
        maintainer="Bulat Gaifullin",
        maintainer_email="gaifullinbf@gmail.com",
        url='https://bitbucket.org/kab00m/storm',
        license='MIT',
        long_description=readme(),
        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: Other Environment",
            "License :: OSI Approved :: MIT License",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: OS Independent",
            "Operating System :: POSIX",
            "Operating System :: POSIX :: Linux",
            "Operating System :: Unix",
            "Programming Language :: Python :: 3.4",
            "Topic :: WEB",
        ],
    )
