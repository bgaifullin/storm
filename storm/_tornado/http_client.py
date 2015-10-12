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


from tornado.httpclient import HTTPRequest, AsyncHTTPClient, HTTPResponse, HTTPError
from tornado.httputil import HTTPHeaders, url_concat

from . import _cookiejar

__all__ = ['HTTPClient', 'HTTPResponse']


class HTTPClient:
    ErrorClass = HTTPError

    def __init__(self, settings):
        AsyncHTTPClient.configure(None, defaults=settings)
        self.client = AsyncHTTPClient()
        self.cookies = _cookiejar.CookieJar()

    url_concat = staticmethod(url_concat)

    def extract_cookies(self, response):
        if response.exception() is None:
            self.cookies.extract_cookies(response.result())

    def fetch(self, method, url, body, headers, callback=None, **kwargs):
        """executes rest-request asynchronously."""

        headers = HTTPHeaders(**headers)
        request = HTTPRequest(url=url, method=method, body=body, headers=headers, **kwargs)
        self.cookies.add_cookies(request)
        future = self.client.fetch(request, callback=callback)
        future.add_done_callback(self.extract_cookies)
        return future
