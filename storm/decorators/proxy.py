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


def _transfer_response(context, response):
    """copy http_response to context"""
    context.set_status(response.code)
    context.write(response.body)
    for n, v in response.headers.get_all():
        context.add_header(n, v)


# def proxy(func):
#     """proxying the urlfetch response"""
#     _future_class = asyncio.Future
#     _async = asyncio.async
#     _partial = functools.partial
#     _is_coroutine = asyncio.iscoroutinefunction(func)
#
#     @functools.wraps(func, updated=[])
#     def wrapper(context, **kwargs):
#         if _is_coroutine:
#             result = _async(func(context, **kwargs), loop=context.event_loop)
#         else:
#             result = func(context, **kwargs)
#
#         if isinstance(result, _future_class):
#             return aio_transform1(
#                 _partial(_json_dumps, context), result, loop=context.event_loop
#             )
#
#         _json_dumps(context, result)
#
#     return wrapper
