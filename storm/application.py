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

import warnings
from collections import defaultdict

from . import framework
from .resources import traverse

_ARRAY = (tuple, list)


class OverwrittenWarning(Warning):
    def __init__(self, url, method):
        super().__init__('%s %s is overwritten' % (method.upper(), url))


class _Routes:
    def __init__(self):
        self.handlers = defaultdict(dict)

    def _add_method(self, url, name, func):
        """adds method for url"""
        if isinstance(name, _ARRAY):
            for n in name:
                self._add_method(url, n, func)

        name = str.lower(name)
        methods = self.handlers[url]
        if name in methods:
            warnings.warn(OverwrittenWarning(url, name))
        methods[name] = func

    def add(self, method, url, func):
        """adds a new url handler to routes"""
        if isinstance(url, _ARRAY):
            for u in url:
                self.add(u, method, func)
            return
        self._add_method(url.lower(), method, func)

    def get(self):
        """returns the handlers"""
        return self.handlers.items()


def ishandler(h):
    """checks that h is handler."""
    return callable(h) and hasattr(h, '__handler__')


def start(*packages, prefix='/', **kwargs):
    """
    launch application, not return until exit
    :param packages: the list of packages to find handlers
    :param prefix: the uri prefix
    :param kwargs: the parameters that will be passed to Tornado application
    """

    requires = set()
    known_exceptions = dict()
    routes = _Routes()
    options = list()
    seen_options = set()
    _empty_list = list()

    def consumer(unit):
        requires.update(getattr(unit, 'REQUIRES', _empty_list))
        known_exceptions.update(getattr(unit, 'EXCEPTIONS', _empty_list))
        for opt in getattr(unit, 'SETTINGS', _empty_list):
            if not opt['name'] in seen_options:
                seen_options.add(opt['name'])
                options.append(opt)

        for m in filter(ishandler, vars(unit).values()):
            m(routes)

    traverse(packages, consumer)

    modules = []
    for name in requires:
        module = framework.import_object("%s.modules.%s" % (__package__, name))
        known_exceptions.update(getattr(module, 'EXCEPTIONS', _empty_list))
        modules.append(module)

    kwargs.setdefault('known_exceptions', dict()).update(known_exceptions)
    framework.start_serve(prefix, options, modules, routes.get(), **kwargs)
