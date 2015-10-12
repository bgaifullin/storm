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
import ujson
import urllib.parse as urllib_parse

import tornado.auth
import tornado.httpclient as httpclient
from tornado.httputil import url_concat


AuthError = tornado.auth.AuthError


class ContextMixin:
    def __init__(self, context):
        self.context = context

    def __getattr__(self, item):
        return getattr(self.context, item)


class GoogleOAuth2(tornado.auth.OAuth2Mixin, ContextMixin):
    """Google authentication using OAuth2."""

    _OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/auth"
    _OAUTH_ACCESS_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
    _API_ENDPOINT = "https://www.googleapis.com/plus/v1/people"
    _OAUTH_NO_CALLBACKS = False

    @tornado.auth.return_future
    def authenticate(self, redirect_uri, callback,
                     code=None, client_id=None, client_secret=None):
        """Handles the login for the Google user, returning a user object."""
        http = self.get_auth_http_client()
        body = urllib_parse.urlencode({
            "redirect_uri": redirect_uri,
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
        })

        http.fetch(self._OAUTH_ACCESS_TOKEN_URL,
                   functools.partial(self._on_access_token, callback),
                   method="POST", headers={'Content-Type': 'application/x-www-form-urlencoded'}, body=body)

    @staticmethod
    def _on_access_token(callback, response):
        """Callback function for the exchange to the access token."""
        if response.error:
            raise AuthError("Google auth error: %s(%s)" % (response.error, response.body))
        try:
            session = ujson.loads(response.body)
        except ValueError as e:
            raise AuthError("Google auth error: %s" % e) from None

        callback(session)

    @tornado.auth.return_future
    def google_request(self, path, callback, **kwargs):
        """call the relative google plus apis."""

        url = self._API_ENDPOINT + path
        if kwargs:
            url = url_concat(url, kwargs)

        http = self.get_auth_http_client()
        http.fetch(url, callback=functools.partial(self._on_google_request, callback))

    @staticmethod
    def _on_google_request(callback, response):
        if response.error:
            raise AuthError("Error response %s(%s) fetching %s" %
                            (response.error, response.body, response.request.url))

        try:
            data = ujson.loads(response.body)
        except ValueError as e:
            raise AuthError("Error response: %s fetching %s" % (e, response.request.url)) from None

        callback(data)

    @staticmethod
    def get_auth_http_client():
        return httpclient.AsyncHTTPClient()
