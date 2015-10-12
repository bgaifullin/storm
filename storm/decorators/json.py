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

import asyncio
import functools
import ujson

from ..utilities import convert1


CONTENT_TYPE = 'application/json'
CHARSET = 'UTF-8'

_empty_result = {'_json': None}


def _json_dumps(context, data):
    if not context.finished:
        indent = bool(context.get_argument('pretty', None)) << 1
        context.set_header('Content-Type', '%s; charset=%s' % (CONTENT_TYPE, CHARSET))
        context.write(ujson.dumps(data, sort_keys=True, indent=indent).encode(CHARSET))
        context.finish()


def _json_input(func):
    """decodes json from body and pass as keyword argument"""

    @functools.wraps(func, updated=[])
    def wrapper(context, **kwargs):
        body = context.get_request_body()
        if len(body) != 0:
            actual_content_type, charset = context.get_content_type()
            if actual_content_type != CONTENT_TYPE:
                return context.send_error(415, reason="Content-Type should be \"%s\"" % CONTENT_TYPE)

            if len(charset) > 0 and charset != CHARSET:
                return context.send_error(415, reason="charset should be \"%s\"" % CHARSET)

            try:
                kwargs['_json'] = ujson.loads(body)
            except ValueError as e:
                return context.send_error(400, reason=str(e))

        return func(context, **kwargs)
    return wrapper


def _json_output(func):
    """serializes output as json"""
    _future_class = asyncio.Future
    _async = asyncio.async
    _partial = functools.partial
    _is_coroutine = asyncio.iscoroutinefunction(func)

    @functools.wraps(func, updated=[])
    def wrapper(context, **kwargs):
        if _is_coroutine:
            result = _async(func(context, **kwargs), loop=context.modules.loop)
        else:
            result = func(context, **kwargs)

        if isinstance(result, _future_class):
            return convert1(
                _partial(_json_dumps, context), result, loop=context.modules.loop
            )

        _json_dumps(context, result)

    return wrapper


def json(func):
    """processes json input and output"""
    return _json_output(_json_input(func))


json.output = _json_output
