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

import signal

from tornado import web

from . import handler
from . import log


def _options_callback(func, context):
    def wrapper():
        func(**context)
        context.clear()
    return wrapper


class ModulesRegistry:
    def __init__(self, loop, logger):
        self.loop = loop
        self.logger = logger

    @staticmethod
    def _load_module(registry, name, loader, options, loop, logger):
        settings = {k[len(name) + 1:]: v for k, v in options.group_dict(name).items()}
        registry[name] = loader(settings, loop=loop, logger=logger)
        logger.info("the module %s has been loaded successfully.", name)

    def lazy_load(self, module, options):
        name = module.__name__.split('.')[-1]
        for opt in module.SETTINGS:
            options.define(name='_'.join((name, opt.pop('name'))), group=name, **opt)

        options.add_parse_callback(_options_callback(
            self._load_module,
            {
                'registry': self.__dict__,
                'loader': module.load,
                'name': name,
                'loop': self.loop,
                'logger': self.logger,
                'options': options
            })
        )


def _get_event_loop():
    from tornado.platform.asyncio import AsyncIOMainLoop
    loop = AsyncIOMainLoop()
    loop.install()
    return loop


def _concat_url(base, uri):
    if uri.startswith('/'):
        return uri
    return base + uri


def compile_handler(methods):
    return type("Handler%d" % id(methods), (handler.TemplateHandler,), methods)


def start(prefix, settings, modules, routes, known_exceptions, **kwargs):
    """starts the tornado application.
    :param prefix: the url prefix
    :param settings: the user defined settings
    :param modules: the modules to load
    :param handlers: the list of url routes (url, handler)
    :param known_exceptions: the mapping of known exceptions to HTTP codes
    :param kwargs: the tornado application arguments
    """
    from tornado.options import options

    options.define("config", type=str, help="path to config file",
                   callback=lambda p: options.parse_config_file(p, final=False))
    options.define("port", default=8000, help="listening port", type=int)
    options.define("address", default='127.0.0.1', help="listening address")

    options.add_parse_callback(log.patch_logger)

    loop = _get_event_loop()
    modules_registry = ModulesRegistry(loop.asyncio_loop, log.gen_log)

    for module in modules:
        modules_registry.lazy_load(module, options)

    for opt in settings:
        options.define(**opt)

    options.parse_command_line(final=True)

    if not prefix.endswith('/'):
        prefix += '/'

    kwargs.update(options.group_dict('application'))
    kwargs.setdefault('default_handler_class', handler.DefaultHandler)
    # prevent override this option
    kwargs['known_exceptions'] = known_exceptions
    kwargs['modules'] = modules_registry

    handlers = []
    for uri, methods in routes:
        log.app_log.info("add resource: %s", uri)
        handlers.append((_concat_url(prefix, uri), compile_handler(methods)))

    app = web.Application(handlers, **kwargs)
    app.listen(options.port, options.address, xheaders=True)

    signal.signal(signal.SIGTERM, lambda *x: loop.stop())
    log.app_log.info("start listening on %s:%d", options.address, options.port or 80)

    try:
        loop.start()
    except (KeyboardInterrupt, SystemExit):
        pass

    loop.close()
    log.app_log.info("gracefully shutdown.")
