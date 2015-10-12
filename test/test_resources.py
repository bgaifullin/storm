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
from pathlib import Path
from unittest import mock

from storm import framework
from storm import resources


class TestResources(unittest.TestCase):
    def test_import_object(self):
        module = resources._import_object("unittest")
        self.assertIs(unittest, module)
        submodule = resources._import_object("storm.resources")
        self.assertIs(submodule, resources)
        attr = resources._import_object("unittest.TestCase")
        self.assertIs(attr, unittest.TestCase)

    @mock.patch('inspect.stack')
    def test_get_package(self, stack):
        stack.return_value = [[
            framework.ObjectDict({'f_locals': {'__name__': '__main__'}}),
            resources.__file__
        ]]
        sys_path = list()
        with mock.patch('sys.path', new=sys_path):
            module_path, module_name = resources._get_package('./modules')

        self.assertEqual(
            [str(Path(resources.__file__).parent / 'modules')],
            module_path
        )
        self.assertEqual('storm.modules', module_name)
        self.assertEqual(str(Path(resources.__file__).parents[1]), sys_path[0])

    @mock.patch('storm.resources._get_package')
    def test_resolve_packages(self, get_package):
        storm_path = Path(resources.__file__).parent
        get_package.return_value = str(storm_path), 'storm'

        self.assertEqual(
            get_package.return_value,
            next(resources._resolve_packages(['./storm']))
        )

        self.assertEqual(
            ([str(storm_path / 'decorators')], 'storm.decorators'),
            next(resources._resolve_packages(['storm.decorators']))
        )

        self.assertEqual(
            (str(storm_path / 'resources.py'), 'storm.resources'),
            next(resources._resolve_packages(['storm.resources']))
        )

        with self.assertRaisesRegex(RuntimeError, "package not found"):
            next(resources._resolve_packages("storm.Adelina"))

    @mock.patch('storm.resources._get_package')
    def test_traverse(self, get_package):
        modules = set()
        resources._traverse(resources.__file__, 'storm.resources', modules.add)
        self.assertEqual({resources}, modules)
        modules.clear()
        resources._traverse(
            [str(Path(resources.__file__).parent / 'decorators')], 'storm.decorators',
            lambda x: modules.add(x.__name__)
        )
        self.assertIn('storm.decorators.argparser', modules)

        get_package.return_value = [(str(Path(resources.__file__).parent / 'decorators'), 'storm.decorators')]
        modules.clear()
        resources.traverse(['storm.decorators'], lambda x: modules.add(x.__name__))
        self.assertIn('storm.decorators.argparser', modules)
