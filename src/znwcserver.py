#!/usr/bin/python3
import json
import sys

import requests

if __name__ == '__main__':
    if len(sys.argv) > 1:
        url = sys.argv[1]
        try:
            res = requests.get(url)
            m = {
                'err': 0,
                'status_code': res.status_code,
                # Final URL location of Response.
                'url': res.url,
                'elapsed': res.elapsed.total_seconds() * 1000,
            }
        except requests.exceptions.HTTPError:
            m = {'err': 1, 'err_str': 'HTTP Error'}
        except requests.exceptions.SSLError:
            m = {'err': 2, 'err_str': 'SSL Error'}
        except requests.exceptions.ConnectTimeout:
            m = {'err': 3, 'err_str': 'Connect Timeout'}
        except requests.exceptions.ReadTimeout:
            m = {'err': 4, 'err_str': 'Read Timeout'}
        except requests.exceptions.ConnectionError:
            m = {'err': 5, 'err_str': 'Connection Error'}
        except requests.exceptions.TooManyRedirects:
            m = {'err': 6, 'err_str': 'Too Many Redirects'}

        except requests.exceptions.MissingSchema:
            m = {'err': 7, 'err_str': 'Missing Schema'}
        except requests.exceptions.InvalidSchema:
            m = {'err': 8, 'err_str': 'Invalid Schema'}
        except requests.exceptions.InvalidURL:
            m = {'err': 9, 'err_str': 'Invalid URL'}
        except requests.exceptions.InvalidHeader:
            m = {'err': 10, 'err_str': 'Invalid Header'}
        except BaseException:
            m = {'err': 1000, 'err_str': 'Unknown Error'}

        print(json.dumps(m))
