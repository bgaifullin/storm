"""
This file is part of Storm

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

import unittest
import warnings
from unittest import mock

from storm import application


class PackageStub:
    def __init__(self,
                 exceptions=None,
                 requires=None,
                 settings=None):

        self.REQUIRES = requires
        self.EXCEPTIONS = exceptions
        self.SETTINGS = settings


def _traverse_mock(p, consumer):
    for i in p:
        consumer(i)


class TestApplication(unittest.TestCase):

    def test_add_url(self):
        func = lambda x: None
        routes = application._Routes()
        routes.add("Get", "/test", func)
        self.assertEqual({"/test": {"get": func}}, routes.handlers)
        with warnings.catch_warnings(record=True) as log:
            routes.add("Get", "/test", func)
            self.assertEqual(1, len(log))
            self.assertIs(application.OverwrittenWarning, log[0].category)
            self.assertIn("GET /test is overwritten", str(log[0].message))

        routes.handlers.clear()
        routes.add(["Get", "post"], ("/test", "test"), func)
        self.assertEqual(
            {"/test": {"get": func, "post": func}, "test": {"get": func, "post": func}},
            routes.handlers
        )

    @mock.patch.multiple("storm.application",
                         traverse=_traverse_mock,
                         framework=mock.DEFAULT)
    def test_start(self, framework):
        package = PackageStub(
            {
                ValueError: 400,
                RuntimeError: lambda x: 400
            },
            ("m1",),
            [
                {"name": "test"}
            ]
        )

        framework.import_object.return_value = 'm1'

        application.start(package, package)

        framework.import_object.assert_called_once_with(
            "storm.modules.m1"
        )
        framework.start_serve.assert_called_once_with(
            "/",
            package.SETTINGS, ["m1"],
            dict([]).items(),
            known_exceptions=package.EXCEPTIONS
        )
