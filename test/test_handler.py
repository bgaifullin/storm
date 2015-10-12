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
from unittest import mock

from storm import handler


class _Registry:
    def __init__(self):
        self.items = list()

    def add(self, *args):
        self.items.extend(args)


class TestResources(unittest.TestCase):
    def test_register(self):
        registry = _Registry()
        args = ['get', '/test/', lambda: None]
        handler._register(registry, *args)
        self.assertEqual(args, registry.items)

    @mock.patch('storm.handler.decorators')
    def test_apply_mutation(self, decorators):
        decorators.mutation1.return_value = 2
        decorators.mutation2.return_value = 3
        self.assertEqual(3, handler._apply_mutation(1, "mutation1,mutation2,"))
        decorators.mutation1.assert_called_once_with(1)
        decorators.mutation2.assert_called_once_with(2)
        self.assertEqual(1, handler._apply_mutation(1, None))
        self.assertEqual(1, handler._apply_mutation(1, ''))

    @mock.patch('storm.handler.argparser')
    def test_apply_argparser(self, argparser):
        def test_func(p1, _p2, p3, p4s, p5: int, k1=2, k2: str=None, k3=None, k4s=2, _k5=0):
            del p1, _p2, p3, p4s, p5, k1, k2, k3, k4s, _k5

        handler._apply_argparser(test_func)
        argparser.argparser.assert_called_once_with([
            ('p3', None, False),
            ('p4s', None, True),
            ('p5', int, False),
            ('k1', int, False, 2),
            ('k2', str, False, None),
            ('k3', None, False, None),
            ('k4s', int, False, 2),
        ])

        argparser.argparser.return_value.assert_called_once_with(test_func)

    @mock.patch.multiple('storm.handler',
                         _apply_argparser=mock.DEFAULT,
                         _apply_mutation=mock.DEFAULT,
                         _handler=mock.DEFAULT)
    def test_declare(self, _apply_argparser, _apply_mutation, _handler):
        _apply_mutation.return_value = 'f1'
        _apply_argparser.return_value = 'f2'
        _handler.handler.return_value = 'f3'
        h = handler.declare('get', '/test', mutator='m', secure=False, status=200)('f0')
        self.assertTrue(h.__handler__)
        _apply_mutation.assert_called_once_with('f0', 'm')
        _apply_argparser.assert_called_once_with('f1')
        _handler.handler.assert_called_once_with('f2', secure=False, status=200)
        registry = _Registry()
        h(registry)
        self.assertEqual(['get', '/test', 'f3'], registry.items)
