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

import sys
import os


def _import_object(name):
    """import object"""
    if name.count('.') == 0:
        return __import__(name, None, None)

    parts = name.split('.')
    obj = __import__('.'.join(parts[:-1]), None, None, [parts[-1]], 0)
    try:
        return getattr(obj, parts[-1])
    except AttributeError:
        raise ImportError("No module named %s" % parts[-1])


def _get_package(path):
    """
    :param path: the system path to package
    :return: system path and package name
    """

    if path.startswith(os.path.curdir) and not os.path.exists(path):
        # try to get full path by stack
        import inspect
        for frame in inspect.stack():
            if frame[0].f_locals.get('__name__') == "__main__":
                path = os.path.join(os.path.dirname(os.path.realpath(frame[1])), path)
                break

    path = os.path.abspath(path)
    modules = []
    if path.endswith(".py"):
        fullpath = path
        modules.append(os.path.basename(path)[:-3])
        path = os.path.dirname(path)
    else:
        fullpath = [path]

    if path.endswith(os.path.sep):
        path = path[:-1]

    while True:
        if not os.path.exists(os.path.join(path, "__init__.py")):
            if path not in sys.path:
                sys.path.insert(0, path)
            break

        modules.append(os.path.basename(path))
        path = os.path.dirname(path)

    modules.reverse()

    return fullpath, '.'.join(modules)


def _resolve_packages(packages):
    """resolve full package path according to sys.path"""
    for package in packages:
        if os.path.sep in package:
            path, package = _get_package(package)
            yield path, package
        else:
            for sp in sys.path:
                path = os.path.join(sp, package.replace('.', os.path.sep))
                if os.path.isdir(path):
                    yield [path], package
                    break
                path += ".py"
                if os.path.isfile(path):
                    yield path, package
                    break
            else:
                raise RuntimeError("package not found: %s" % package)


def _traverse(path, package, consumer):
    """
    Walk through specified packages and build handlers list
    :param path: the root path
    :param package:  the package object
    :param consumer: the descriptor consumer
    """
    import pkgutil

    def import_package(n):
        if package:
            n = '.'.join((package, n))
        return _import_object(n)

    if isinstance(path, str):
        children = [(_import_object(package), False)]
    else:
        children = map(lambda x: (import_package(x[1]), x[2]), pkgutil.iter_modules(path))
    for child in filter(None, children):
        consumer(child[0])
        if child[1]:
            _traverse(child[0].__path__, child[0].__package__, consumer)


def traverse(packages, consumer):
    """traverse list of packages and collect descriptors"""
    for path, package in _resolve_packages(packages):
        _traverse(path, package, consumer)
