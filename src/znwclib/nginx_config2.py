import re
import sys
from collections import ChainMap
from typing import Union, List, Tuple

import crossplane
import validators


class NginxDirective:
    def __init__(self, block: list):
        self.block = block

    def directiveIter(self, directiveName: str):
        """
        Возвращает итератор директив с именем directiveName
        :param directiveName:
        :return:
        """
        for directive in self.block:
            if directive.get('directive') == directiveName:
                yield directive

    def checkDirectiveExists(self, directiveName: str) -> bool:
        for directive in self.directiveIter(directiveName):
            if directive:
                return True
        return False

    def getDirectiveArgs(self, directiveName: str):
        for directive in self.directiveIter(directiveName):
            if directive:
                yield directive.get('args')


class NginxLocation(NginxDirective):
    _re_patt_port = re.compile(r"^\s*([^:]+):\s+(.+)$")
    _re_patt_assignment = re.compile(r"^\s*(.+)\s+=\s+(.+)$")
    _re_patt_split = re.compile(r"[\s,]+")

    def __init__(self, url: Union[str, tuple, list], block: list, server, parent=None):
        super().__init__(block)
        self.url = url if isinstance(url, str) else ''.join(url)

        if not isinstance(server, NginxServer):
            raise ValueError("Invalid parameter server")

        self.server: NginxServer = server  # server directive for this location

        if parent and not isinstance(parent, NginxLocation):
            raise ValueError("Invalid parameter parent")

        self.parent: NginxLocation = parent if parent else server  # parent location/server directive

        self._replaces = {}  # special comments  'replace:'
        self._variables = {}  # special comments 'var:'
        self._varsChainMap = None  # _variables ChainMap with parent
        self.replace_all = None  # special comment 'replace_all:'
        self.skip_this = False  # special comment 'skip_this:'
        self._processSpecialComments()
        if parent:  # processing URL only for location not for server
            self._processLocationURL()
        else:  # for server add $hostname variable
            self.variables['$hostname'] = self.server.http.hostname
        self._processSubLocations()

        self._returnDirective = None  # cache for return directive

    def __repr__(self):
        return f"NginxLocation(URL={self.url})"

    def __str__(self):
        return self.url

    @property
    def variables(self) -> Union[ChainMap, dict]:
        """
        :return: Свои переменные и переменные родителя
        """
        if self.parent == self:  # this is server directive
            return self._variables
        if self._varsChainMap is None:
            self._varsChainMap = ChainMap(self._variables, self.parent._variables)
        return self._varsChainMap

    def _processLocationURL(self) -> str:
        """
        Заменяет в self.url переменные на имеющиеся в self.variables
        """
        if self.url.startswith('='):
            self.url = self.url[1:]
        elif self.url.startswith('^~'):
            self.url = self.url[2:]

        for var in self.variables:
            self.url = self.url.replace(var, self.variables[var])
        return self.url

    @property
    def returnDirective(self) -> Tuple[int, str]:
        # TODO: переписать с использованием self.getDirectiveArgs
        if self._returnDirective is None:
            for directive in self.directiveIter('return'):
                args = directive.get('args')
                if args:
                    if len(args) == 2:
                        self._returnDirective = (int(args[0]), args[1])
                    if len(args) == 1:
                        self._returnDirective = (302, args[0])
            else:
                self._returnDirective = (-1, '')
        return self._returnDirective

    @property
    def isStubStatus(self):
        return self.checkDirectiveExists('stub_status')

    @property
    def isRewriteRule(self):
        return self.checkDirectiveExists('rewrite')

    @property
    def validSubLocations(self):
        root_location_exist = False
        for nginxLoc in self._subLocations:
            if nginxLoc.checkLocationIsValid():
                for nginxLocNext in nginxLoc.validSubLocations:
                    yield nginxLocNext
                yield nginxLoc
        # raise StopIteration

    @property
    def validSubLocationsLen(self):
        return sum(1 for _ in self.validSubLocations)

    def checkLocationIsValid(self) -> bool:
        """
        Проверяем на валидность директиву listen
        :return:
        """
        if self.server.http.skipLocations and self.url != '/':  # do not process locations
            return False

        if self.returnDirective[0] > self.server.http.retCode:  # if  directive return code more than
            return False
        if not self.url:  # empty url
            return False
        if self.url.startswith('~'):  # we can't process regexpr locations
            return False
        if self.url.startswith('@'):  # we can't process @named locations
            return False
        if self.url.startswith('/.well-known/acme-challenge'):  # skip acme bot locations
            return False
        if self.isStubStatus:  # check stub_status directive
            return False
        if self.isRewriteRule:  # check for rewrite rule directive
            # TODO: надо подумать как обрабатывать эту штуку. Пока просто игнорим ее
            return False
        return True  # all checks pass

    def _processSubLocations(self):
        """"
        запховываем location directives в список, чтобы потом обработать
        """
        self._subLocations = [
            NginxLocation(directive['args'], directive['block'], self.server, self.parent)
            for directive in self.directiveIter('location')
        ]

    def _processSpecialComments(self):
        """
        Обрабатывает комментарии и ищет специальные, по ним составляет словарь
        Примеры специальных комментариев:
            # replace: <changed_name> = changed_name[, another_changed_name[, ...]]
            # replace_all: <replaced str>
            # var: $<name_of_var = <value_of_var>
            # skip_this: True
        """
        for directive in self.block:
            if directive.get('directive', '') == '#':
                m = NginxLocation._re_patt_port.match(directive['comment'])
                if m:
                    cmd, cmd_val = m.group(1, 2)
                    if cmd == 'skip_this' and cmd_val == 'True':
                        self.skip_this = True
                    if cmd == 'replace_all':
                        self.replace_all = NginxLocation._re_patt_split.split(cmd_val)
                    elif cmd == 'replace':
                        m = NginxLocation._re_patt_assignment.match(cmd_val)
                        if m:
                            key, val = m.group(1, 2)
                            self._replaces[key] = NginxLocation._re_patt_split.split(val)
                    elif cmd == 'var':
                        m = NginxLocation._re_patt_assignment.match(cmd_val)
                        if m:
                            key, val = m.group(1, 2)
                            self._variables[key] = val


class NginxServer(NginxLocation):
    _re_patt_listen_port = re.compile(r"(^|:)(?P<port>\d+)$")

    def __init__(self, http, block: list):
        self.http: NginxHttp = http
        super().__init__('', block, self)
        if not self.skip_this:
            # Check for deprecated directive ssl on|off
            self.sslOn = \
                any(True for sslArgs in self.getDirectiveArgs('ssl') if sslArgs[0] == 'on') or \
                any(True for sslArgs in self.http.getDirectiveArgs('ssl') if sslArgs[0] == 'on')
            self.names = self._prepNames()
            self.test = 1

    def _prepNames(self):
        """
        Готовим имена серверов
        :return:
        """

        def prepName(_name: str) -> str:
            """
            Заменяем имена на из replace
            После подставляем переменные из variables
            :param _name:
            :return:
            """
            if self._replaces.get(_name):
                _name = self._replaces[_name]
            for var in self.variables:
                _name = _name.replace(var, self.variables[var])

            if _name.startswith('*.'):
                _name = f"www{_name[1:]}"
            elif _name.startswith('.'):
                _name = _name[1:]
            return _name

        if self.replace_all:
            return self.replace_all
        else:
            result = []
            for names in self.getDirectiveArgs('server_name'):
                for name in names:
                    name = prepName(name)
                    if validators.domain(name) or validators.ipv4(name) or validators.ipv6(name):
                        result.append(name)
            return result

    @property
    def listens(self):
        """
        Возвращает все listen директивы в виде (<номер порта>, <http|https>)
        :return:
        """
        for listenArgs in self.getDirectiveArgs('listen'):
            protocol = 'https' if self.sslOn else 'http'
            port = self.http.defPort
            for arg in listenArgs:
                if arg == 'ssl':
                    protocol = 'https'
                elif arg.startswith('so_keepalive'):
                    # пропускаем, т.к. может попасть под следующее регулярное выражение
                    pass
                else:
                    res = NginxServer._re_patt_listen_port.search(arg)
                    if res:
                        port = int(res.group('port'))
                        # bellow dirty hack. may be wrong may be true
                        # 443 порт without ssl directive
                        if port == 443:
                            protocol = 'https'
            yield port, protocol,

    @property
    def serverURLsStr(self):
        """
         возвращает комбинации names и listens в виде списка url
        :return: generator
        """
        for listen in self.listens:
            for name in self.names:
                server_name_url = f"{listen[1]}://{name}"
                if listen not in ((80, 'http'), (443, 'https')):
                    server_name_url = f"{server_name_url}:{listen[0]}"
                yield server_name_url

    @property
    def serverURLsLocationsStr(self):
        """
        комбинируем self.serverURLsStr и self.validSubLocations
        :return:
        """
        for server_url in self.serverURLsStr:
            root_location_exist = False
            for location in self.validSubLocations:
                if location.url == '/':
                    root_location_exist = True
                yield f"{server_url}{location.url}"
            if not root_location_exist:
                yield server_url


class NginxHttp(NginxDirective):
    def __init__(self, block: list, hostname: str,
                 defPort=80,
                 retCode=399,
                 skipLocations=False,
                 dnsCheck=False,
                 skipPermanentRedirects=True
                 ):
        super().__init__(block)
        self.skipPermanentRedirects = skipPermanentRedirects
        self.hostname = hostname
        self.defPort = defPort
        self.retCode = retCode
        self.skipLocations = skipLocations
        self.dnsCheck = dnsCheck
        self.servers = [NginxServer(self, directive['block']) for directive in self.directiveIter('server')]

    @property
    def urls(self) -> List[str]:
        return []


if __name__ == '__main__':
    pl = crossplane.parse('../test.conf/kidsapp/nginx.conf', comments=True, combine=True, ignore=('types', 'events',))
    if pl['status'] == 'failed':
        # return 'Error: ' + ', '.join([err['error'] for err in pl['errors']])
        print("Error")
    config = pl['config'][0]['parsed']
    for d in config:
        if d['directive'] == 'http':
            http_block = d['block']
            break
    else:
        print("Error: something wrong")
        sys.exit(-1)

    httpObj = NginxHttp(http_block, 'hbz.ru')
    for server in httpObj.servers:
        print("====================\nServer:")
        print(', '.join(server.serverURLsStr))
        print("------------\nLocatioins")
        print(', '.join(loc for loc in server.serverURLsLocationsStr))

    print("Success")
