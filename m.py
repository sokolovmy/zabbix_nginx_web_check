#!/usr/bin/python3

from crossplane import parse

NDIRECTIVES = ('http', 'server', 'location', 'include', 'listen', 'server_name', 'return', 'proxy_pass', 'fastcgi_pass')
skipDirectives = ('types', 'events',)

if __name__ == "__main__":

    pl = parse('./nginx-cfg/nginx.conf', comments=True, combine=False, ignore=tuple(skipDirectives))
    config = pl['config'][0]['parsed']
    # looking for a directive http
    for d in config:
        if d['directive'] == 'http':
            http = d['block']
            break
    servers = []
    for d in http:
        if d['directive'] == 'server':
            servers.append(d['block'])

    print(servers)
