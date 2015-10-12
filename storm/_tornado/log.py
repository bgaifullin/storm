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

import logging
import logging.handlers
from tornado import log
import time

app_log = log.app_log
gen_log = log.gen_log


class LogFormatter(log.LogFormatter):
    default_time_format = '%Y-%m-%dT%H:%M:%S'
    default_msec_format = '.%03d'

    DEFAULT_FORMAT = '%(color)s[%(levelname)1.1s %(asctime)s %(request)s]%(end_color)s %(message)s'
    DEFAULT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
    DEFAULT_MSEC_FORMAT = '.%03d'

    def __init__(self, color=True, fmt=DEFAULT_FORMAT,
                 datefmt=DEFAULT_DATE_FORMAT):
        super().__init__(color, fmt, datefmt)

    def formatTime(self, record, datefmt=None):
        """format time according to ISO-8601"""
        ct = self.converter(record.created)
        t = time.strftime(datefmt or self.DEFAULT_DATE_FORMAT, ct)
        s = self.DEFAULT_MSEC_FORMAT % record.msecs
        z = time.strftime('%z', ct) or 'Z'
        return t + s + z

    def format(self, record):
        record.__dict__.setdefault('request', '')
        return super().format(record)


def patch_logger(logger=None):
    """patches logger handlers"""
    if logger is None:
        logger = logging.getLogger()
    for h in logger.handlers:
        h.setFormatter(LogFormatter())
