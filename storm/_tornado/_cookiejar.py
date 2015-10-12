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

from http import cookiejar
from urllib.parse import urlsplit
import logging
import time

_logger = logging.getLogger('flash.cookie_jar')


def request_host(request):
    """Return request-host, as defined by RFC 2965.

    Variation from RFC: returned value is lowercased, for convenient
    comparison.

    """
    host = urlsplit(request.url).hostname
    if host == "":
        host = request.get_header("Host", "").partition(":")[0]

    # remove port, if present
    return host.lower()


def eff_request_host(request):
    """Return a tuple (request-host, effective request-host name).

    As defined by RFC 2965, except both are lowercased.

    """
    erhn = req_host = request_host(request)
    if req_host.find(".") == -1 and not cookiejar.IPV4_RE.search(req_host):
        erhn = req_host + ".local"
    return req_host, erhn


def extract_scheme(url):
    """Return the request scheme"""
    return urlsplit(url, "http").scheme


def extract_port(url):
    """the port component of request.url"""
    port = urlsplit(url).port
    if port is None:
        port = cookiejar.DEFAULT_HTTP_PORT
    return port


def extract_path(url):
    """Path component of url."""
    parts = urlsplit(url)
    path = cookiejar.escape_path(parts.path)
    if not path.startswith("/"):
        # fix bad RFC 2396 absoluteURI
        path = "/" + path
    return path


def check_domain(domain, request):
    # Liberal check of.  This is here as an optimization to avoid
    # having to load lots of MSIE cookie files unless necessary.
    req_host, erhn = eff_request_host(request)
    if not req_host.startswith("."):
        req_host = "." + req_host
    if not erhn.startswith("."):
        erhn = "." + erhn

    return req_host.endswith(domain) or erhn.endswith(domain)


def check_path(path, request):
    return extract_path(request.url).startswith(path)


_UNSET = object()


class CookieJar:
    def __init__(self):
        self._cookies = dict()

    @staticmethod
    def _normalized_cookie_tuples(attr_set):
        """Return list of tuples containing normalised cookie information.

        attrs_set is the list of lists of key,value pairs extracted from
        the Set-Cookie or Set-Cookie2 headers.

        Tuples are name, value, standard, rest, where name and value are the
        cookie name and value, standard is a dictionary containing the standard
        cookie-attributes (discard, secure, version, expires or max-age,
        domain, path and port) and rest is a dictionary containing the rest of
        the cookie-attributes.

        """
        cookie_tuples = []

        boolean_attrs = "discard", "secure"
        value_attrs = ("version",
                       "expires", "max-age",
                       "domain", "path", "port",
                       "comment", "commenturl")

        for cookie_attrs in attr_set:
            name, value = cookie_attrs[0]

            # Build dictionary of standard cookie-attributes (standard) and
            # dictionary of other cookie-attributes (rest).

            # Note: expiry time is normalised to seconds since epoch.  V0
            # cookies should have the Expires cookie-attribute, and V1 cookies
            # should have Max-Age, but since V1 includes RFC 2109 cookies (and
            # since V0 cookies may be a mish-mash of Netscape and RFC 2109), we
            # accept either (but prefer Max-Age).
            max_age_set = False

            bad_cookie = False

            standard = {}
            rest = {}
            for k, v in cookie_attrs[1:]:
                lc = k.lower()
                # don't lose case distinction for unknown fields
                if lc in value_attrs or lc in boolean_attrs:
                    k = lc
                if k in boolean_attrs and v is None:
                    # boolean cookie-attribute is present, but has no value
                    # (like "discard", rather than "port=80")
                    v = True
                if k in standard:
                    # only first value is significant
                    continue
                if k == "domain":
                    if v is None:
                        _logger.debug("missing value for domain attribute")
                        bad_cookie = True
                        break
                    # RFC 2965 section 3.3.3
                    v = v.lower()
                if k == "expires":
                    if max_age_set:
                        # Prefer max-age to expires (like Mozilla)
                        continue
                    if v is None:
                        _logger.debug("missing or invalid value for expires attribute: treating as session cookie")
                        continue
                if k == "max-age":
                    max_age_set = True
                    try:
                        v = int(v)
                    except ValueError:
                        _logger.debug(" missing or invalid (non-numeric) value for max-age attribute")
                        bad_cookie = True
                        break
                    # convert RFC 2965 Max-Age to seconds since epoch
                    # XXX Strictly you're supposed to follow RFC 2616
                    #   age-calculation rules.  Remember that zero Max-Age is a
                    #   is a request to discard (old and new) cookie, though.
                    k = "expires"
                    v += int(time.time())
                if (k in value_attrs) or (k in boolean_attrs):
                    if v is None and k not in ("port", "comment", "commenturl"):
                        _logger.debug("missing value for %s attribute" % k)
                        bad_cookie = True
                        break
                    standard[k] = v
                else:
                    rest[k] = v

            if bad_cookie:
                continue

            cookie_tuples.append((name, value, standard, rest))

        return cookie_tuples

    def _cookie_from_cookie_tuple(self, cookies_tuple, response):
        # standard is dict of standard cookie-attributes, rest is dict of the
        # rest of them

        now = int(time.time())
        name, value, standard, rest = cookies_tuple

        domain = standard.get("domain", _UNSET)
        path = standard.get("path", _UNSET)
        port = standard.get("port", _UNSET)
        expires = standard.get("expires", _UNSET)

        # set the easy defaults
        version = standard.get("version", None)
        if version is not None:
            try:
                version = int(version)
            except ValueError:
                return None  # invalid version, ignore cookie
        secure = standard.get("secure", False)
        # (discard is also set if expires is Absent)
        discard = standard.get("discard", False)
        comment = standard.get("comment", None)
        comment_url = standard.get("commenturl", None)

        # set default path
        if path is not _UNSET and path != "":
            path_specified = True
            path = cookiejar.escape_path(path)
        else:
            path_specified = False
            path = extract_path(response.effective_url)
            i = path.rfind("/")
            if i != -1:
                if version == 0:
                    # Netscape spec parts company from reality here
                    path = path[:i]
                else:
                    path = path[:i + 1]
            if len(path) == 0:
                path = "/"

        # set default domain
        domain_specified = domain is not _UNSET
        # but first we have to remember whether it starts with a dot
        domain_initial_dot = False
        if domain_specified:
            domain_initial_dot = bool(domain.startswith("."))
        if domain is _UNSET:
            domain = eff_request_host(response.request)[1]
        elif not domain.startswith("."):
            domain = "." + domain

        # set default port
        port_specified = False
        if port is not _UNSET:
            if port is None:
                # Port attr present, but has no value: default to request port.
                # Cookie should then only be sent back on that port.
                port = extract_port(response.effective_url)
            else:
                try:
                    port = int(port.strip())
                    port_specified = True
                except ValueError:
                    _logger.debug("invalid port")
                    port = None

        else:
            # No port attr present.  Cookie can be sent back on any port.
            port = None

        # set default expires and discard
        if expires is _UNSET:
            expires = None
            discard = True
        elif expires <= now:
            # Expiry date in past is request to delete cookie.  This can't be
            # in DefaultCookiePolicy, because can't delete cookies there.
            try:
                self.clear(domain, path, name)
            except KeyError:
                pass
            return None

        return cookiejar.Cookie(version,
                                name, value,
                                port, port_specified,
                                domain, domain_specified, domain_initial_dot,
                                path, path_specified,
                                secure,
                                expires,
                                discard,
                                comment,
                                comment_url,
                                rest)

    def clear(self, domain=None, path=None, name=None):
        """Clear some cookies.

        Invoking this method without arguments will clear all cookies.  If
        given a single argument, only cookies belonging to that domain will be
        removed.  If given two arguments, cookies belonging to the specified
        path within that domain are removed.  If given three arguments, then
        the cookie with the specified name, path and domain is removed.

        Raises KeyError if no matching cookie exists.

        """
        _logger.debug("Expiring cookie, domain='%s', path='%s', name='%s'", domain, path, name)

        if name is not None:
            if (domain is None) or (path is None):
                raise ValueError("domain and path must be given to remove a cookie by name")
            del self._cookies[domain][path][name]
        elif path is not None:
            if domain is None:
                raise ValueError(
                    "domain must be given to remove cookies by path")
            del self._cookies[domain][path]
        elif domain is not None:
            del self._cookies[domain]
        else:
            self._cookies = dict()

    def parse_cookies(self, response):
        # get cookie-attributes for RFC 2965 and Netscape protocols
        headers = response.headers
        ns_headers = headers.get_list("Set-Cookie")

        if not ns_headers:
            return []

        try:
            cookies_tuple = self._normalized_cookie_tuples(cookiejar.parse_ns_headers(ns_headers))
            return [self._cookie_from_cookie_tuple(cookie_tuple, response) for cookie_tuple in cookies_tuple]
        except Exception as e:
            _logger.warning("Unexpected error: %r", e)
            return []

    def set_cookie(self, cookie):
        """Set a cookie, without checking whether or not it should be set."""
        c = self._cookies
        if cookie.domain not in c:
            c[cookie.domain] = {}
        c2 = c[cookie.domain]
        if cookie.path not in c2:
            c2[cookie.path] = {}
        c3 = c2[cookie.path]
        c3[cookie.name] = cookie

    @staticmethod
    def unparse_cookie(cookie):
        # What should it be if multiple matching Set-Cookie headers have
        #  different versions themselves?
        # Answer: there is no answer; was supposed to be settled by
        #  RFC 2965 errata, but that may never appear...
        # add cookie-attributes to be returned in Cookie header

        if cookie.value is None:
            return cookie.name
        else:
            return "%s=%s" % (cookie.name, cookie.value)

    def extract_cookies(self, response):
        for cookie in self.parse_cookies(response):
            self.set_cookie(cookie)

    def add_cookies(self, request):
        _now = int(time.time())
        req_secure = extract_scheme(request.url) == "https"
        req_port = extract_port(request.url)

        expired = []
        cookies = []
        for domain in self._cookies:
            if not check_domain(domain, request):
                continue

            for path in self._cookies[domain]:
                if not check_path(path, request):
                    continue

                for cookie in self._cookies[domain][path].values():
                    if cookie.is_expired(_now):
                        expired.append(cookie)
                        continue

                    if cookie.secure and not req_secure:
                        continue

                    if cookie.port_specified and cookie.port != req_port:
                        continue

                    cookies.append(cookie)

            cookies.sort(key=lambda a: len(a.path), reverse=True)
            headers = request.headers
            if "Cookie" in headers:
                exists_cookies = headers['Cookie']
                if len(exists_cookies) > 0 and not exists_cookies.endswith('; '):
                    exists_cookies += '; '
            else:
                exists_cookies = ''

            request.headers["Cookie"] = exists_cookies + "; ".join(self.unparse_cookie(c) for c in cookies)

            for cookie in expired:
                self.clear(cookie.domain, cookie.path, cookie.name)
