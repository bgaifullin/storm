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
from .. import utilities


EXCEPTIONS = {
    framework.auth.AuthError: 400,
}

SETTINGS = [
    {
        "name": "api_key",
        "help": "The google application key"
    },
    {
        "name": "secret",
        "help": "The google application secret"
    },
]


class GoogleClient:
    def __init__(self, client, session, loop=None):
        self.client = client
        self.sesion = session
        self.loop = loop

    def __google_request(self, path, **kwargs):
        """requests to google."""
        kwargs['access_token'] = self.sesion['access_token']
        return utilities.convert1(
            None,
            self.client.google_request(path, **kwargs),
            loop=self.loop
        )

    def get_user_info(self, fields=None):
        # TODO check lifetime
        return self.__google_request("/me", fields=fields)


class GoogleConnector:
    def __init__(self, client_id, client_secret, loop):
        self.client_id = client_id
        self.client_secret = client_secret
        self.loop = loop

    def grant_access(self, context, redirect_uri, scope=None, response_type=None, extra_params=None):
        """grants access"""
        client = framework.auth.GoogleOAuth2(context)
        return utilities.convert1(
            None,
            client.authorize_redirect(
                redirect_uri,
                client_id=self.client_id,
                client_secret=self.client_secret,
                scope=scope,
                response_type=response_type,
                extra_params=extra_params
            ),
            loop=self.loop
        )

    def authenticate(self, context, redirect_uri, code):
        """authenticates on google and returns client"""
        client = framework.auth.GoogleOAuth2(context)
        return utilities.convert1(
            functools.partial(GoogleClient, client, loop=self.loop),
            client.authenticate(
                redirect_uri, code=code, client_id=self.client_id, client_secret=self.client_secret
            ),
            loop=self.loop
        )


def load(options, loop, **_):
    return GoogleConnector(
        options['api_key'],
        options['secret'],
        loop=loop
    )
