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

from .. import framework


class InvalidArgumentTypeError(framework.HTTPError):
    """Exception raised by `_get_argument`.

    This is a subclass of `HTTPError`, so if it is uncaught a 400 response
    code will be used instead of 500 (and a stack trace will not be logged).
    """
    def __init__(self, arg_name, arg_type):
        super().__init__(400, 'Invalid type of argument %s, expected %s' % (arg_name, arg_type.__name__))
        self.arg_name = arg_name
        self.arg_type = arg_type


class MissingArgumentError(framework.HTTPError):
    """Exception raised by `RequestHandler.get_argument`.

    This is a subclass of `HTTPError`, so if it is uncaught a 400 response
    code will be used instead of 500 (and a stack trace will not be logged).
    """
    def __init__(self, arg_name):
        super(MissingArgumentError, self).__init__(400, 'Missing argument %s' % arg_name)
        self.arg_name = arg_name


_UNSET = object()

class _ArgumentParser:
    """Class to parse request arguments"""

    def __init__(self, name=None, converter=None, multiple=False, default=_UNSET):
        self.name = name
        self.multiple = multiple
        self.converter = converter
        self.default = default

    def _convert(self, v):
        if self.converter is None:
            return v
        try:
            return self.converter(v)
        except (ValueError, TypeError):
            raise InvalidArgumentTypeError(self.name, self.converter)

    def __call__(self, context, path_args):
        """acquires argument from context"""

        name = self.name
        if path_args and name in path_args:
            return self._convert(path_args[name])

        value = context.get_arguments(name)
        if not value:
            if self.default is _UNSET:
                raise MissingArgumentError(name)
            return self.default
        if self.multiple:
            value = [self._convert(x) for x in value]
        else:
            value = self._convert(value[-1])
        return value


def argparser(arguments):
    """declare input arguments"""
    def add_parser(func):

        parsers = tuple(_ArgumentParser(*x) for x in arguments)

        @functools.wraps(func, updated=[])
        def wrapped(context, **kwargs):
            kwargs = {p.name: p(context, kwargs) for p in parsers}
            return func(context, **kwargs)
        return wrapped

    return add_parser
