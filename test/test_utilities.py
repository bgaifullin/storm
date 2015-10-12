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

import unittest
import asyncio

from storm import utilities


class TestUtilities(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()

    def tearDown(self):
        super().tearDown()
        self.loop.stop()
        self.loop.close()

    def test_convert2(self):
        f = asyncio.Future(loop=self.loop)
        f.set_result(1)
        r = utilities.convert2(str, f, asyncio.Future(loop=self.loop))
        self.loop.run_until_complete(r)
        self.assertEqual('1', r.result())

    def test_convert1(self):
        f = asyncio.Future(loop=self.loop)
        f.set_result('1')
        r = utilities.convert1(int, f, loop=self.loop)
        self.loop.run_until_complete(r)
        self.assertEqual(1, r.result())
