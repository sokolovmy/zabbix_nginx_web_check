import re
from typing import Optional, Union, Tuple

import crossplane
import dns.exception
import dns.resolver
import validators

_re_patt_port = re.compile(r"^\s*([^:]+):\s+(.+)$")
_re_patt_assignment = re.compile(r"^\s*(.+)\s+=\s+(.+)$")
_re_patt_split = re.compile(r"[\s,]+")
_re_patt_listen_port = re.compile(r"(^|:)(?P<port>\d+)$")


def process_special_comments(directives_list: list, hostname_var: str) -> dict:
    """
    Обрабатывает комментарии и ищет специальные, по ним составляет словарь
    Примеры специальных комментариев:
        # replace: <changed_name> = changed_name[, another_changed_name[, ...]]
        # replace_all: <replaced str>
        # var: $<name_of_var = <value_of_var>
        # skip_this: True
    :param hostname_var: $hostname - variable
    :param directives_list:  - список директив в {}
    :rtype: dictionary
    """
    replaces = {}
    variables = {
        '$hostname': hostname_var
    }
    res = {
        'replace': replaces,
        'var': variables
        # 'replace_all': str - appear if it's founded
        # 'skip_this': True - appear if it's founded
    }
    for directive in directives_list:
        if directive.get('directive', '') == '#':
            m = _re_patt_port.match(directive['comment'])
            if m:
                cmd, cmd_val = m.group(1, 2)
                if cmd == 'skip_this' and cmd_val == 'True':
                    res['skip_this'] = True
                if cmd == 'replace_all':
                    res['replace_all'] = _re_patt_split.split(cmd_val)
                elif cmd == 'replace':
                    m = _re_patt_assignment.match(cmd_val)
                    if m:
                        key, val = m.group(1, 2)
                        replaces[key] = _re_patt_split.split(val)
                elif cmd == 'var':
                    m = _re_patt_assignment.match(cmd_val)
                    if m:
                        key, val = m.group(1, 2)
                        variables[key] = val
    return res


def prep_name_var(name: str, special_comments: dict) -> str:
    """
    Заменяет в имени name переменные на имеющиеся в special_comments
    :param name:
    :param special_comments:
    :return:
    """
    if special_comments and special_comments.get('var'):
        variables = special_comments['var']
        for var in variables:
            name = name.replace(var, variables[var])
    return name


def prep_server_name(name: str, special_comments: dict, single=False) -> Union[str, list, None]:
    """
    Обрабатывает имя сервера используя словарь специальных комментариев
    см. функции get_server_name
    :param name: обрабатываемое имя
    :param special_comments: словарь подготовленный process_special_comments
    :param single: если server_name содержит одно имя (используется для замены '' на $hostname)
    :return:
    """
    res = special_comments['replace'].get(name, [])
    res = [n for n in res if validators.domain(n)]
    if res:
        return res

    name = prep_name_var(name, special_comments)
    if len(name) == 0 and single:
        return special_comments['var']['$hostname']

    if name.startswith('*.'):
        name = f"www{name[1:]}"
    elif name.startswith('.'):
        name = name[1:]

    return name if validators.domain(name) else None


def get_server_names(server_block: list, hostname_var: str, special_comments: dict = None) -> Optional[list]:
    """
        check server_name directive & return tuple of server names

        Имена из директивы server_name, такие как:
          - *.example.org - по умолчанию будут заменены на www.example.org,
          - .example.org - будет заменено на example.org,
          - www.example.* - удаляется, т.к. невозможно точно предсказать какие имена в реальности будут использованы,
          - ~^www\..+\.example\.org$ - все регулярные выражения также будут удаляться.
          - "" - удаляется, если значение не является единственным в списке, в противном случае заменяется на $hostname
          - имена *, _, --, !@# и другие некорректные имена удаляются из списка
        Можно изменить поведение обработчика, если указать специальные комментарии непосредственно
        под директивой server_name.
            # replace: <changed_name> = changed_name[, another_changed_name[, ...]]
        изменяет одно имя на список
            # replace_all: changed_name[, another_changed_name[, ...]]
        заменяет все имена в директиве на список имен из комментария
            # var: $<name_of_var = <value_of_var>
        заменяет все вхождения переменной на то, что будет указано в комментарии
        переменную $hostname можно не указывать, по умолчанию, она устанавливается в имя сервера на котором запускается
        скрипт либо ее можно указать при вызове скрипта через параметр командной строки
        Сначала имена заменяются из replace:, далее подставляются переменные.
        Если есть replace_all: все replace: & var: игнорируются
        Если есть skip_this: возвращается None, дальнейшая обработка прекращается

        Примеры
        # replace: *.example.org = my_site_name.example.org another_site_name.example.org etc.example.org`
        # replace: .example.org = www.example.org
        # replace_all: www.example.org
        # var: $Host = my_site.domain.com
        # var $Hostname = another_my_site_name.domain.com

    :param server_block: словарь возвращаемый crossplane.parse из директивы server
    :param special_comments: словарь подготовленный process_special_comments
    :param hostname_var: $hostname
    :returns возвращает кортеж имен из директивы server_name
    """
    server_names = []
    if special_comments is None:
        special_comments = process_special_comments(server_block, hostname_var)

    if special_comments.get('skip_this'):
        return None
    elif special_comments.get('replace_all'):
        return special_comments['replace_all']

    for directive in server_block:
        if directive.get('directive', '') == 'server_name':
            args = directive['args']
            if args:
                single = len(args) == 1
                for arg in args:
                    server_name = prep_server_name(arg, special_comments, single)
                    if server_name:
                        if isinstance(server_name, str):
                            server_names.append(server_name)
                        else:
                            server_names.extend(server_name)
    # make unique, not fast but works
    server_names = list(dict.fromkeys(server_names))
    return server_names if server_names else [hostname_var]


def check_ssl_on(server_block: list):
    """
        checks deprecated directive ssl on|off
        need check on http, server block
    :param server_block:
    :return: True  - if ssl on | False if not found or ssl off;
    """
    for d in server_block:
        dd = d['directive']
        if dd == 'ssl':
            if 'on' in d['args']:
                return True
    return False


def get_listen(listen_args, default_port=80, server_ssl_on=False):
    """
    Обрабатывает аргумент директивы listen

    :param server_ssl_on: deprecated directive ssl on|off on http & server blocks, but still using
    :param default_port: порт по умолчанию nginx (если под root 80, если нет 8000)
    :param listen_args список аргументов директивы listen
    :return (<номер порта>, <(http|https)>)
    """
    protocol = 'https' if server_ssl_on else 'http'
    port = default_port
    for arg in listen_args:
        if arg == 'ssl':
            protocol = 'https'
        elif arg.startswith('so_keepalive'):
            # пропускаем, т.к. может попасть под следующую регулярное выражение
            pass
        else:
            res = _re_patt_listen_port.search(arg)
            if res:
                port = int(res.group('port'))
                # bellow dirty hack. may be wrong may be true
                # 443 порт without ssl directive
                if port == 443:
                    protocol = 'https'

    return port, protocol,


def get_all_listen_directives(server_block, default_port=80, server_ssl_on=False):
    """

    :param server_block:
    :param default_port:
    :param server_ssl_on: deprecated directive ssl on|off on http & server blocks, but still using
    :return: list[tuple[int, str]]
    """

    listens = []
    for d in server_block:
        if d['directive'] == 'listen':
            listens.append(get_listen(d['args'], default_port, server_ssl_on))

    return listens


def prepare_location(location_args: list, location_block: list, special_comments: dict) -> Optional[str]:
    """
    Подготовка location's
    не поддерживаются: ~, ~* - location's с регулярными выражением, а также именованные @Loc_name
    если в комментариях нет им замены они будут пропущены
    Чтобы заменить можно использовать
        # replace_all: <new location>
        если представлен список, то берется первое значение из списка
    Чтобы пропустить обработку можно написать в комментариях
       #  skip_this: True
    :param location_block:
    :param location_args:
    :param special_comments:
    """
    if special_comments:
        if special_comments.get('skip_this'):
            return None
        elif special_comments.get('replace_all'):
            return special_comments['replace_all'][0]

    location = ''.join(location_args)

    if not location:
        return None

    if location.startswith('~'):
        # checks ~ and ~*
        return None

    if location.startswith('='):
        location = location[1:]
    elif location.startswith('^~'):
        location = location[2:]
    location = prep_name_var(location, special_comments)
    # skip acme bot locations
    if location.startswith('/.well-known/acme-challenge'):
        return None
    if location.startswith('@'):
        return None

    # check stub_status directive
    for d in location_block:
        if d.get('directive') == 'stub_status':
            return None

    return location


def skip_on_return(block: list, return_code) -> bool:
    for d in block:
        dd = d['directive'].lower()
        if dd == 'return':
            da = d['args']
            if len(da) > 0:
                try:
                    return_code_from_directive = int(da[0])
                except ValueError:
                    return False

                return return_code_from_directive > return_code

    return False


def get_locations(server_block: list, hostname_var, return_code=399) -> Tuple[list, bool]:
    """
    Выдает список location's из блока server. Вложенные location's также добавляются в список.
    Не включаются в список, если return http code больше return_code
    Не поддерживаются location's выполненные в виде регулярных выражений (~, ~*) и именованные (@Named),
    их можно заменить при помощи специальных комментариев

    Специальные комментарии должные быть расположены внутри блока location:
        # replace_all: <changed location>
        # skip_this: True
        # var: $var_name = var_value
        # var: @another_var_name = var_value

    :rtype: object
    :param server_block: блок server crossplane.parse
    :param hostname_var: переменная $hostname
    :param return_code:
    :return:
    """
    locations: list = []
    for d in server_block:
        dd = d['directive'].lower()
        if dd == 'location':
            da = d['args']
            db = d.get('block')
            special_comments = process_special_comments(db, hostname_var)
            location = prepare_location(da, db, special_comments)
            if db and skip_on_return(db, return_code):
                if location == '/':
                    return [], True
                continue
            if location:
                locations.append(location)
            nested_locations, _ = get_locations(db, hostname_var, return_code)
            if nested_locations:
                locations.extend(nested_locations)

    return locations, False


def delFileLine(block: list):
    """
    for debug deleting file & line from directives dict
    :param block:
    :return:
    """
    for directive in block:
        directive.pop('file', None)
        directive.pop('line', None)
        if directive.get('block'):
            delFileLine(directive['block'])


def process_servers(html_block: list, hostname_var, default_port=80, return_code=399, skip_locations=False,
                    debug=False):
    """
    Обрабатывает html block crossplane.parse. возвращает список словарей в котором лежат server_name's & location's

    Не включаются в список, если в директиве return http_code больше return_code

    Поддерживаются специальные комментарии:
        # replace: server_name = changed_server_name[, another_server_name[, ...]]
        имя из списка будет заменено на другое. Имена проверяются на корректность.
        # replace_all: changed_name[, another_changed_name[, ...]]
        вся строка с именами будет заменена на новую. Проверка на корректность не производится
        # skip_this: True
        пропустить этот сервер
        # var: $var_name = var_value
        # var: @another_var_name = var_value
    Переменные встречающиеся в именах будут заменены в соответствии с вышеописанным списком

    Имена из директивы server_name, такие как:
          - *.example.org - по умолчанию будут заменены на www.example.org,
          - .example.org - будет заменено на example.org,
          - www.example.* - удаляется, т.к. невозможно точно предсказать какие имена в реальности будут использованы,
          - ~^www\..+\.example\.org$ - все регулярные выражения также будут удаляться.
          - "" - удаляется, если значение не является единственным в списке, в противном случае заменяется на $hostname
          - имена *, _, --, !@# и другие некорректные имена удаляются из списка
    Любое имя, в том числе некорректное, может быть заменено с помощью специальных комментариев на другое.

    :param debug: for debug purposes
    :param skip_locations: не обрабатывать блоки locations
    :param html_block: html block from crossplane.parse
    :param default_port: default listen port
    :param hostname_var: variable $hostname
    :param return_code: если встречается директива return и код больше, чем указан, сервер пропускается
    :rtype: list[{
                'server_names': tuple[str],
                'locations': tuple[str],
                'listen': tuple[str],
                }]
    """
    ret_val = []
    ssl_on = check_ssl_on(html_block)
    for d in html_block:
        if d['directive'] == 'server':
            server_block = d['block']
            if skip_on_return(server_block, return_code):
                continue
            ssl_on = ssl_on or check_ssl_on(server_block)
            server_names = get_server_names(server_block, hostname_var)
            if server_names:
                locations, skip_root = get_locations(server_block, hostname_var, return_code)
                if skip_root:
                    continue
                server = {
                    'server_names': server_names,
                    'locations': locations if not skip_locations else [],
                    'listens': get_all_listen_directives(server_block, default_port, ssl_on)
                }
                if debug:
                    server['debug'] = server_block
                ret_val.append(server)
    return ret_val


def check_exist_host_name_dns(host_name):
    try:
        dns.resolver.resolve(host_name)
        return True
    except dns.exception.DNSException:
        return False


def get_URLs_from_config(config_file_name: str, hostname_var: str, default_port: int = 80,
                         return_code: int = 399, skip_locations=False, dns_check=False, debug=False):
    pl = crossplane.parse(config_file_name, comments=True, combine=True, ignore=('types', 'events',))
    if pl['status'] == 'failed':
        return 'Error: ' + ', '.join([err['error'] for err in pl['errors']])
    config = pl['config'][0]['parsed']
    # looking for a directive http
    # http_block = None
    for d in config:
        if d['directive'] == 'http':
            http_block = d['block']
            break
    else:
        # something wrong
        return "Error: something wrong"

    #    if debug:
    #       delFileLine(http_block)
    res = process_servers(http_block, hostname_var, default_port, return_code, skip_locations, debug=debug)
    # servers0_answer = [{
    #         'locations': ['/hbz', '/equal', '/if_equal_not_check_regexpr', '/namedLocation/to/hbz_value'],
    #         'server_names': ('hbz.ru',),
    #         'listens': [(80, 'http')],
    #     }]
    urls = []
    for server in res:
        for listen in server['listens']:
            for server_name in server['server_names']:
                if dns_check and not check_exist_host_name_dns(server_name):
                    continue
                server_name_url = f"{listen[1]}://{server_name}"
                if listen not in ((80, 'http'), (443, 'https')):
                    server_name_url = f"{server_name_url}:{listen[0]}"
                if not debug:
                    urls.append(server_name_url)
                else:
                    urls.append((server_name_url, server['debug']))

                if not skip_locations:
                    for location in server['locations']:
                        if location == '/':
                            # already added server_name url
                            continue
                        if location and not location.startswith('/'):
                            location = f"/{location}"
                        if not debug:
                            urls.append(server_name_url + location)
                        else:
                            urls.append((server_name_url + location, server['debug']))

    return urls
