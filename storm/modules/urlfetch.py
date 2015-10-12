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
from urllib.parse import urljoin

from .. import framework


EXCEPTIONS = {
    framework.HTTPClient.ErrorClass: lambda x: x.code,
}


SETTINGS = [
    {
        "name": "root_ca",
        "help": "the root certificate file"
    },
    {
        "name": "validate_cert",
        "help": "validate the server certificate"
    },
    {
        "name": "client_cert",
        "help": "the client certificate"
    },
    {
        "name": "client_key",
        "help": "he client private key"
    },
    {
        "name": "retries",
        "help": "the default retries count"
    },
]


class HTTPClient:
    def __init__(self, retries=None, loop=None, **kwargs):
        self.client = framework.HTTPClient(kwargs)
        self.retries = retries
        self.loop = loop

    def fetch(self, context, url, args=None, method=None, data=None, headers=None, retries=None, **kwargs):
        """
        executes rest-request asynchronously
        :param context: the RequestContext
        :param url: the url or url components object or url
        :param args: the query arguments
        :param method: the request method
        :param data: the request body
        :param headers: the custom headers
        :param kwargs: see framework.HTTPClient.urlfetch for details
        """
        if retries is None:
            retries = self.retries

        if method is None:
            method = 'GET' if data is None else 'POST'

        if headers is None:
            headers = dict()

        if isinstance(url, tuple):
            url = urljoin(*url)

        if args is not None:
            url = self.client.url_concat(url, args)

        headers["Referer"] = context.get_full_url()
        logger = context.logger

        def set_default_content_type(content_type):
            if "Content-Type" not in headers:
                headers["Content-Type"] = content_type

        if isinstance(data, dict):
            set_default_content_type("application/json; charset=utf-8")
            data = ujson.dumps(data).encode('utf8')
        elif isinstance(data, str):
            set_default_content_type("text/plain; charset=utf-8")
            data = data.encode('utf8')
        elif isinstance(data, bytes):
            set_default_content_type("octet/binary")
        else:
            raise ValueError("unsupported type of data - %s" % type(data))

        future = asyncio.Future(loop=self.loop)
        client = self.client

        def done_callback(retries_, response):
            error = response.error

            if error is None:
                body = response.body
                content_type, _, charset = response.headers['Content-Type'].lower().partition(';')
                if len(body) > 0 and content_type == 'application/json':
                    try:
                        response.json = ujson.loads(body.decode(charset.lower() or 'utf-8'))
                    except ValueError as e:
                        future.set_exception(e)

                if not future.done():
                    future.set_result(response)
            else:
                if isinstance(error, client.ErrorClass):
                    if error.code > 500 or retries_ == 0:
                        future.set_exception(error)
                else:
                    future.set_exception(error)

            if future.done():
                logger.info(
                    "HTTP request %d %s %02.f (%d)", response.code, url, response.request_time, retries - retries_
                )
            else:
                client.fetch(
                    method, url, data=data, headers=headers,
                    callback=functools.partial(done_callback, retries_ - 1), **kwargs
                )

        client.fetch(
            method, url, data=data, headers=headers,
            callback=functools.partial(done_callback, retries), **kwargs
        )

        return future


def load(options, **_):
    """load urlfetch module"""
    import sys

    def load_cert(fname):
        if fname is not None:
            try:
                with open(options.root_ca, 'rb') as stream:
                    return stream.read()
            except FileNotFoundError as e:
                print(e, file=sys.stderr)

    return HTTPClient(user_agent="WebEngine-UrlFetch",
                      ca_certs=load_cert(options['root_ca']),
                      client_key=load_cert(options['client_key']),
                      client_cert=load_cert(options['client_cert']),
                      validate_cert=options['validate_cert'],
                      retries=options['retries'])
