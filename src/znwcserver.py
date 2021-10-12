import socket

import requests
import dns.resolver

if __name__ == '__main__':
    sres = socket.getaddrinfo('haulmont.ru', 0)
    dres = dns.resolver.resolve('ost-admin.haulmont.ru')
    res = requests.get('http://www.haulmont.ru')
    print(res)
