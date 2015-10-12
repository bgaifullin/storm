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

import wsql


EXCEPTIONS = {
    wsql.DataError: 400,
    wsql.InterfaceError: 503,
}

SETTINGS = [
    {
        "name": "master",
        "default": "localhost",
        "multiple": True,
        "help": "the master nodes: hostname[:port][#count], (can be repeated)"
    },
    {
        "name": "slave",
        "default": "",
        "multiple": True,
        "help": "the slave nodes: hostname[:port][#count] (can be repeated)"
    },
    {
        "name": "user",
        "default": "root",
        "help": "username to connect to database as"
    },
    {
        "name": "password",
        "default": "",
        "help": "password to connect to database"
    },
    {
        "name": "database",
        "default": "test",
        "help": "database to use"
    },
    {
        "name": "timeout",
        "default": 5,
        "help": "connection timeout"
    },
    {
        "name": "retries",
        "default": 1,
        "help": "the number of retries"
    },
    {
        "name": "delay",
        "default": 1,
        "help": "the delay between retries in seconds"
    },
    {
        "name": "charset",
        "default": "utf8",
        "help": "the database charset"
    },
]


def load(options, loop, logger):
    """load the database module"""

    from wsql.converters import object_row_decoder
    import wsql.cluster

    options["row_formatter"] = object_row_decoder

    return wsql.cluster.connect(options, loop=loop, logger=logger)
