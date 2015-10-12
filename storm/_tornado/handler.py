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
import uuid
from itertools import filterfalse

import tornado.web
import ujson


logger = logging.getLogger(__package__.split('.', 1)[0])


def _split_locales(locales):
    """
    Split locale to locale and language
    """
    for code in locales:
        yield code
        yield code.partition('-')[0].lower()


class RequestHandler(tornado.web.RequestHandler):
    """The request context"""

    SUPPORTED_METHODS = frozenset(tornado.web.RequestHandler.SUPPORTED_METHODS)

    _logger = None

    @property
    def finished(self):
        """indicates that request has been finished yet."""
        return self._finished

    @property
    def logger(self):
        """Get the request specific logger."""
        return self._logger

    @property
    def modules(self):
        return self.settings['modules']

    def request_uri(self):
        """Shortcut for request.uri."""
        return self.request.uri

    def get_full_url(self):
        """Shortcut for request.full_url."""
        return self.request.full_url()

    def get_full_path(self):
        request = self.request
        return request.protocol + "://" + request.host + request.path

    def get_body(self):
        """Shortcut for request.body."""
        return self.request.body

    def get_content_type(self):
        """Shortcut to get content-type and charset"""
        content_type, _, charset = self.get_header("Content-Type", "").partition(';')
        return content_type.strip().lower(), charset.strip().partition("=")[-1].upper()

    def get_browser_languages(self, default="en_US"):
        """Determines the user's locale and language from ``Accept-Language`` header.
        See http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.4
        """

        languages = self.get_header("Accept-Language", None)
        if languages:
            languages = languages.split(",")
        else:
            languages = [default]

        locales = []
        for language in languages:
            parts = language.strip().split(";")
            if len(parts) > 1 and parts[1].startswith("q="):
                try:
                    score = float(parts[1][2:])
                except (ValueError, TypeError):
                    score = 0.0
            else:
                score = 1.0
            locales.append((parts[0], score))
        if locales:
            locales.sort(key=lambda pair: pair[1], reverse=True)
            seen = set()
            seen_add = seen.add
            for code in filterfalse(seen.__contains__, _split_locales(map(lambda pair: pair[0], locales))):
                seen_add(code)
                yield code

    def initialize(self):
        """see tornado.RequestHandler initialize"""
        request_id = self.get_header('X-REQUEST-ID', None) or str(uuid.uuid4())
        self._logger = logging.LoggerAdapter(logger, {"request": request_id})

    def get_header(self, name, default=None):
        """get the header from request by name"""
        return self.request.headers.get(name, default)

    def _log(self):
        """override"""
        if self.get_status() < 400:
            log_method = self.logger.info
        elif self.get_status() < 500:
            log_method = self.logger.warning
        else:
            log_method = self.logger.error
        request_time = 1000.0 * self.request.request_time()
        log_method("%d %s %.2fms", self.get_status(), self._request_summary(), request_time)

    def log_exception(self, typ, value, tb, _http_error=tornado.web.HTTPError):
        """see the tornado.web.Request log_exception for details"""
        if isinstance(value, _http_error):
            if value.log_message:
                self._logger.warning(
                    "%d %s " + value.log_message, value.status_code, self._request_summary(), *value.args
                )
        else:
            self._logger.error(
                "Uncaught exception: %s, %s", self._request_summary(), (typ, value, tb)
            )

    def write_error(self, status_code, **kwargs):
        """write the error to response"""

        if "exc_info" in kwargs and not self.settings.get("serve_traceback"):
            del kwargs["exc_info"]

        kwargs["status"] = status_code
        kwargs["reason"] = self._reason

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        pretty = bool(self.get_argument('pretty', None))
        self.write(ujson.dumps(kwargs, sort_keys=True, indent=pretty << 1))
        self.finish()

    def data_received(self, chunk):
        """make abstract methods inspector happy"""
        pass


class TemplateHandler(RequestHandler):
    key = "id"

    def get(self, *args, **kwargs):
        """HTTP GET method handler"""
        if self.get_argument(self.key, None) is not None:
            return self.getx(*args, **kwargs)
        return self.query(*args, **kwargs)

    def head(self, **_):
        """HTTP HEAD method handler"""
        self.set_header('Allowed', ','.join(sorted(self.SUPPORTED_METHODS)))

    def getx(self, *args, **kwargs):
        """Get a single object by id"""
        self.send_error(404)

    def query(self, *args, **kwargs):
        """Query a batch of objects"""
        self.send_error(404)


class DefaultHandler(RequestHandler):
    def prepare(self):
        """see tornado.web.RequestHandler.prepare"""
        self.send_error(404, reason='%s - not found.' % self.request_uri())
