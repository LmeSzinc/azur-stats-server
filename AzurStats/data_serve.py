import os
from dataclasses import dataclass
from functools import partial
from http.server import test, SimpleHTTPRequestHandler

from AzurStats.config.config import TEMP_DATA

# Ensure running in Alas root folder
os.chdir(os.path.join(os.path.dirname(__file__), '../'))


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)


@dataclass
class Argument:
    bind: str = '127.0.0.1'
    port: int = 22230
    directory: str = TEMP_DATA


if __name__ == '__main__':
    """
    Serve local data on http://127.0.0.1:22230/
    YOU MUST NOT USE THIS IN PRODUCTION ENVIRONMENT
    """
    args = Argument()
    handler_class = partial(CORSRequestHandler, directory=args.directory)
    test(HandlerClass=handler_class, port=args.port, bind=args.bind)
