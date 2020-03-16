"""
Protocol for handling web requests when working with
an external protocol (e.g. transfer)
"""

import sys
import json
import socket
import threading
from common import utils

# -- Python 2 and 3 have most of the same bells and whistles
# for this but 
if utils.PY3:
    import http.server as http
else:
    import BaseHTTPServer as http

"""
TODO:
- Get a threaded server up that handles a POST for transfers
- Have some kind of simple way to augment the reponse based on
  the package... This could be really powerful
- Also, for the future, think about how to set up a remote
  service with this tech that can just build things because we
  say so! That would be the bee's knees.
"""

def get_lan_node_ip():
    """
    Obtain the active IP of our current node
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('10.1.60.54', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


class _HandlerBase(http.BaseHTTPRequestHandler):
    """
    Base class for simple JSON response utilities when communicating
    with other services.
    """

    endpoint = '' # If you want to only handle a custom path 

    def write_to_response(self, data):
        self.wfile.write(
            bytes(json.dumps(data), 'utf-8')
        )


    def get_post_data(self):
        content_length = int(self.headers['Content-Length'])
        return self.rfile.read(content_length)


    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()


    def do_HEAD(self):
        self._set_headers()


    def do_GET(self):
        raise NotImplementedError("Implement in subclass")


    def do_POST(self):
        raise NotImplementedError("Implement in subclass")


class ServerThread(threading.Thread):
    """
    Thread than handles clean start/shutdown of a HTTTP server 
    """
    def __init__(self, server, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self._server = server
        self._lock = threading.Lock()
        self._active = False


    def __enter__(self):
        self.start()


    def __exit__(self, type, value, traceback):
        self.shutdown()


    @property
    def http_server(self):
        """ :return: The HTTPServer instance """
        return self._server


    def run(self):
        """
        Overloaded to run the serve_forever() function of our server
        class
        """
        with self._lock:
            self._active = True
        self._server.serve_forever()
        with self._lock:
            self._active = False


    def shutdown(self):
        """
        Shutdown the server from another thread safely
        """
        with self._lock:
            if self._active:
                self._server.shutdown()


def new_server(handler_class, port=8456):
    """
    Starts the server_class on a new thread to recieve requests
    while we stay available for other tasks.
    :param handler_class: Subclass of the _HandlerBase that implements
    do_<REST_METHOD>(self)
    :param port: The port to supply this thread.

    :return: ServerThread with additional attributes:
        - http_address: The local address of the endpoint we can ship elsewhere
        - shutdown(): callable to stop the service all together

    :note: The thread has not yet started. call .start() to get the app online
    """
    assert (issubclass(handler_class, _HandlerBase)), \
           "Handler must be _HandlerBase subclass"

    server = http.HTTPServer(('', port), handler_class)
    server_thread = ServerThread(server=server)

    address = get_lan_node_ip() + ":{}/{}".format(port, handler_class.endpoint)
    server_thread.http_address = address

    return server_thread
