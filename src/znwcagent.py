#!/usr/bin/python3
import collections
import sys

from znwclib.nginx_config import get_URLs_from_config

__version__ = '0.1'

import argparse
import socket
import json

_DEBUG = False


def parse_cmd_args(hostname=socket.gethostname(), port=80, return_code=399):
    parser = argparse.ArgumentParser(
        description="Get URLs from nginx config file"
    )
    parser.add_argument('--version', action='version', version='Version is ' + __version__)
    parser.add_argument("config_file",
                        metavar="<config file name>",
                        type=str, nargs='?',
                        help="Path to the nginx config file. "
                             "default: /etc/nginx/nginx.conf",
                        default='/etc/nginx/nginx.conf',
                        )
    parser.add_argument('-u', '--human', default=False, action="store_true",
                        help='Human friendly output format')
    parser.add_argument('-s', '--skip_location', action="store_true",
                        help="Add this key if you don't want to handle locations")
    parser.add_argument('-r', '--ret-code', type=int, default=return_code, metavar='<ret code>',
                        help='Return code. All server and url directives, if they contain return <code>,'
                             ' will not be processed if <code> is greater than <ret code>. Default = ' +
                             str(return_code))
    parser.add_argument('-p', '--port', type=int, default=port, metavar='<port>',
                        help='Specify the default port for server directives for which there is no listen directive.'
                             " Default value = " + str(port))
    parser.add_argument('-H', '--hostname', type=str, metavar='<hostname>', default=hostname,
                        help='Specify the hostname. Default is ' + hostname)
    parser.add_argument('-n', '--check-dns', action='store_true',
                        help='Do Check dns records for names in server_name directive')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_cmd_args()
    urls = get_URLs_from_config(
        config_file_name=args.config_file,
        hostname_var=args.hostname,
        default_port=args.port,
        return_code=args.ret_code,
        skip_locations=args.skip_location,
        dns_check=args.check_dns,
        debug=_DEBUG
    )
    if isinstance(urls, str):
        print(urls, file=sys.stderr)
        sys.exit(-1)
    counter = collections.Counter(urls)
    for_json = []
    for url in urls:
        if not _DEBUG:
            url_dict = {'{#URL}': url}
        else:
            url_dict = {'{#URL}': url[0], '{#DEBUG}': url[1]}
        for_json.append(url_dict)

    print(json.dumps(for_json, indent=(2 if args.human else None)))
    # print(args)
