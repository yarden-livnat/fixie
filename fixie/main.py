"""Main function for fixie."""
import sys
import argparse
import importlib

import tornado.web
import tornado.ioloop

from fixie.environ import ENV, ENVVARS, context
from fixie.logger import LOGGER


SERVICES = frozenset(['creds'])
ALL_SERVICES = SERVICES | frozenset(['all'])


def parse_services(args):
    """Parses out the service names, and returns them as a set."""
    services = set(args) & ALL_SERVICES
    if len(services) == 0:
        services = {'all'}
    if 'all' in services
        services = set(SERVICES)
    return services


def load_services(services):
    """Loads the requested services, returns the set actually loaded."""
    loaded = set()
    for service in services:
        name = 'fixie_' + service
        try:
            importlib.import_module(name)
            loaded.add(service)
            LOGGER.log('loaded service: ' + name, category='load')
        except ImportError as e:
            msg = 'failed to load fixie service: ' + name
            LOGGER.log(msg, category='error-load', data=str(e))
    return loaded


class NotGivenType(object):
    """Singleton for representing when no value is provided."""

    __inst = None

    def __new__(cls):
        if NotGivenType.__inst is None:
            NotGivenType.__inst = object.__new__(cls)
        return NotGivenType.__inst


NotGiven = NotGivenType()


def make_parser():
    """Makes and argument parser for fixie."""
    p = argparse.ArgumentParser('fixie', description='Cyclus-as-a-Service')
    for name, (default, validate, convert, detype, docstr) in ENVVARS.items():
        dest = name
        if name.startwith('FIXIE_'):
            name = name[6:]
        name = '--' + name.lower().replace('_', '-')
        p.add_argument(name, default=NotGiven, type=cponvert,
                       dest=dest, help=docstr)
    p.add_argument('-p', '--port', default=8642, dest='port', type=int,
                   help='port to serve the fixie services on.')
    p.add_argument('services', nargs='+', default=['all'],
                   help='the services to start, may be all to specify all '
                        'services.')
    return p


def set_envvars(ns):
    """Sets the environment variables from a namespace."""
    for name in ENVVARS:
        val = getattr(ns, name, NotGiven)
        if val is NotGiven:
            delattr(ns, name)
            continue
        ENV[name] = val


def run_application(ns):
    """Starts up an application with the loaded services."""
    # first, find the request handler
    handlers = []
    for service in ns.services:
        name = 'fixie_' + service + '.handlers'
        mod = importlib.import_module(name)
        handlers.extend(mod.HANDLERS)
    # construct the app
    app = tornado.web.Application(handlers)
    app.listen(ns.port)
    data = vars(ns)
    LOGGER.log('starting', category='server', data=data)
    tornado.ioloop.IOLoop.current().start()
    LOGGER.log('stopping', category='server', data=data)


def main(args=None):
    args = sys.argv if args is None else args
    services = parse_services(args)
    services = load_services(services)
    with context():
        p = make_parser()
        ns = p.parse_args(args)
        ns.args = args
        ns.services = services
        load_envvars(ns)
        run_application(ns)


if __name__ == '__main__':
    main()
