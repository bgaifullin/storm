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

from .. import framework
from ..utilities import convert2


def coroutine_adapter(func):
    """asyncio.Future -> framework.Future"""

    func = asyncio.coroutine(func)

    if framework.Future is asyncio.Future:
        return func

    @functools.wraps(func, updated=[])
    def decorator(context, **kwargs):
        future = asyncio.async(func(context, **kwargs), loop=context.modules.loop)
        return convert2(None, future, framework.Future())

    return decorator


def _handle_exception(context, e):
    """Handle the exception that occurs upon handle request"""
    known_exceptions = context.settings['known_exceptions']
    error_type = type(e)
    if error_type in known_exceptions:
        status = known_exceptions[error_type]
    else:
        base = next((k for k in known_exceptions if isinstance(e, k)), None)
        if base is not None:
            status = known_exceptions[error_type] = known_exceptions[base]
        else:
            status = 500
            context.logger.exception("Unknown exception: %r", e)

    if callable(status):
        status = status(e)
    if context.finished:
        context.logger.exception("Unexpected error: %r", e)
    else:
        context.send_error(status, reason=getattr(e, 'message', None) or str(e))


def handler(func, secure=True, status=None):
    """the decorator, that makes request handler"""
    is_coroutine = asyncio.iscoroutinefunction(func)
    future_class = asyncio.Future

    @coroutine_adapter
    def wrapper(context, **kwargs):
        if secure and not context.current_user:
            return context.send_error(403)

        try:
            result = func(context, **kwargs)
            if is_coroutine or isinstance(result, future_class):
                yield from result

            if context.finished:
                return

            if status is not None:
                context.set_status(status)
            if isinstance(result, (str, bytes)):
                context.write(result)
        except framework.HTTPError:
            raise
        except Exception as e:
            _handle_exception(context, e)

    return functools.update_wrapper(wrapper, func, updated=[])
