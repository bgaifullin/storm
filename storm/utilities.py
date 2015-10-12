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


def _convert(converter, future1, future2):
    """transforms result for future2 to result for future1"""
    try:
        if converter is None:
            future1.set_result(future2.result())
        else:
            future1.set_result(converter(future2.result()))
    except Exception as e:
        future1.set_exception(e)


def convert2(converter, fut1, fut2):
    """converts the result of fut1 and set to fut2"""
    fut1.add_done_callback(functools.partial(_convert, converter, fut2))
    return fut2


def convert1(converter, future, loop=None):
    """applies converter to the result of future."""

    result = asyncio.Future(loop=loop)
    return convert2(converter, future, result)
