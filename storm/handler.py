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

import functools
import inspect

from . import decorators
from .decorators import argparser
from .decorators import handler as _handler

__all__ = ("declare",)


def _register(registry, method=None, url=None, h=None):
    """registers the method"""
    return registry.add(method, url, h)


def _apply_mutation(func, mutators):
    """applies the wrappers"""
    if mutators:
        for m in filter(None, mutators.split(',')):
            d = decorators
            for attr in m.split('.'):
                d = getattr(d, attr)
            func = d(func)
    return func


def _apply_argparser(func):

    spec = inspect.getfullargspec(inspect.unwrap(func))
    arguments = list()
    # first argument is context
    # args
    defaults_len = spec.defaults and len(spec.defaults) or 0
    args_len = len(spec.args) - defaults_len
    for i in range(1, args_len):
        name = spec.args[i]
        if not name.startswith('_'):
            arguments.append((name, spec.annotations.get(name), name.endswith('s')))

    # kwargs
    for i in range(defaults_len):
        name = spec.args[args_len + i]
        if not name.startswith('_'):
            default = spec.defaults[i]
            if name in spec.annotations:
                annotation = spec.annotations[name]
            elif default is not None:
                annotation = type(default)
            else:
                annotation = None
            arguments.append((name, annotation, False, default))
    return argparser.argparser(arguments)(func)


def declare(method, url, mutator=None, **kwargs):
    """make the method handler"""

    def make_handler(func):
        h = _handler.handler(_apply_argparser(_apply_mutation(func, mutator)), **kwargs)
        r = functools.partial(_register, method=method, url=url, h=h)
        r.__handler__ = True
        return r

    return make_handler
