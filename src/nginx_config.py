import os.path
import re
import sys
from typing import Optional

import crossplane
import validators


def process_special_comments(directives_list: list, hostname_var: str) -> dict:
    """
    Обрабатывает комментарии и ищет специальные, по ним составляет словарь
    Примеры специальных комментариев:
        # replace: <changed_name> = <list of changed names through a space>
        # replace_all: <list of changed names through a space>
        # var: $<name_of_var = <value_of_var>
        # skip_this: True
    :param hostname_var: $hostname - variable
    :param directives_list:  - список директив в {}
    :rtype: dictionary
    """
    res = {
        'replace': dict(),
        'var': {
            '$hostname': hostname_var
        },
        # 'replace_all': str - appear if it's founded
        # 'skip_this': True - appear if it's founded
    }
    patt = re.compile(r"^\s*([^:]+):\s+(.+)$")
    patt_eq = re.compile(r"^\s*(.+)\s+=\s+(.+)$")
    patt_split = re.compile(r"[\s,]+")
    for i in directives_list:
        directive = i.get('directive')
        if directive and directive == '#':
            comment = i.get('comment')
            m = patt.match(comment)
            if m:
                cmd, cmd_val = m.group(1, 2)
                if cmd == 'skip_this' and cmd_val == 'True':
                    res['skip_this'] = True
                if cmd == 'replace_all':
                    res['replace_all'] = tuple(patt_split.split(cmd_val))
                elif cmd == 'replace':
                    m = patt_eq.match(cmd_val)
                    if m:
                        key, val = m.group(1, 2)
                        res['replace'][key] = tuple(patt_split.split(val))
                elif cmd == 'var':
                    m = patt_eq.match(cmd_val)
                    if m:
                        key, val = m.group(1, 2)
                        res['var'][key] = val
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


def prep_server_name(name: str, special_comments: dict, single=False) -> Optional[str]:
    """
    Обрабатывает имя сервера используя словарь специальных комментариев
    см. функции get_server_name
    :param name: обрабатываемое имя
    :param special_comments: словарь подготовленный process_special_comments
    :param single: если server_name содержит одно имя (используется для замены '' на $hostname)
    :return:
    """

    res = special_comments.get(name)
    if res is None:
        name = prep_name_var(name, special_comments)
        len_name = len(name)
        if len_name == 0 and single:
            res = special_comments['var']['$hostname']
        elif len_name > 2 and name[0] == '*' and name[1] == '.' and validators.domain(name[2:]):
            res = f"www{name[1:]}"
        elif len_name > 1 and name[0] == '.' and validators.domain(name[1:]):
            res = name[1:]
        elif validators.domain(name):
            res = name
        else:
            res = None
    return res


def get_server_names(server_block: list, hostname_var: str, special_comments: dict = None) -> Optional[tuple[str, ...]]:
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
            # replace: <changed_name> = <list of changed names through a space>
        изменяет одно имя на список
            # replace_all: <list of changed names through a space>
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

    for i in server_block:
        d = i.get('directive')
        if d and d == 'server_name':
            args = i['args']
            if args:
                single = len(args) == 1
                for arg in args:
                    server_name = prep_server_name(arg, special_comments, single)
                    if server_name:
                        server_names.append(server_name)
    if len(server_names):
        return tuple(server_names)
    else:
        return hostname_var,


def get_listen(listen_args: list[str], default_port=80) -> tuple[int, str]:
    """
        Обрабатывает аргумент директивы listen

    :param default_port: порт по умолчанию nginx (если под root 80, если нет 8000)
    :param listen_args список аргументов директивы listen
    :return (<номер порта>, <(http|https)>)
    """
    patt_port = re.compile(r"(^|:)(?P<port>\d+)$")
    protocol = 'http'
    for arg in listen_args:
        if arg.lower() == 'ssl':
            protocol = 'https'
        elif len(arg) >= 12 and arg[0:12] == 'so_keepalive':
            # пропускаем, т.к. может попасть под следующую регулярное выражение
            pass
        else:
            res = patt_port.search(arg)
            if res:
                default_port = res.group('port')
            default_port = int(default_port)

    return default_port, protocol,


def get_all_listen_directives(server_block: list[dict], default_port=80) -> list[tuple[int, str]]:
    # TODO: написать
    listens = []
    for d in server_block:
        if d['directive'].lower() == 'listen':
            listens.append(get_listen(d['args'], default_port))

    return listens


def prepare_location(location_args: list, special_comments: dict) -> Optional[str]:
    """
    Подготовка location's
    не поддерживаются: ~, ~* - location's с регулярными выражением, а также именованные @Loc_name
    если в комментариях нет им замены они будут пропущены
    Чтобы заменить можно использовать
        # replace_all: <new location>
        если представлен список, то берется первое значение из списка
    Чтобы пропустить обработку можно написать в комментариях
       #  skip_this: True
    :param location_args:
    :param special_comments:
    """
    if special_comments:
        if special_comments.get('skip_this'):
            return None
        elif special_comments.get('replace_all'):
            return special_comments['replace_all'][0]

    for arg in location_args:
        length = len(arg)
        if length == 0:
            continue
        if arg[0] == '=':
            if length == 1:
                continue
            else:
                return prep_name_var(arg[1:], special_comments)
        elif arg[0] == '~':
            # checks ~ and ~*
            return None
        elif length >= 2 and arg[0:2] == '^~':
            if length == 2:
                continue
            else:
                return prep_name_var(arg[2:], special_comments)
        else:
            res = prep_name_var(arg, special_comments)
            if len(res) > 0 and res[0] == '@':
                return None
            else:
                return res
    return None


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


def get_locations(server_block: list, hostname_var, return_code=399) -> list[str]:
    """
    Выдает список location's из блока server. Вложенные location's также.
    Не включаются в список, если return http code больше return_code

    Поддерживаются специальные комментарии:
        # replace_all: <changed location>
        # skip_this: True
        # var: $var_name = var_value
        # var: @another_var_name = var_value
    Не поддерживаются:
        - locations with regular expressions
        - named locations (example: @Named)
    Их можно заменить при помощи специального объявления в комментариях
    :rtype: object
    :param server_block: блок server crossplane.parse
    :param hostname_var: переменная $hostname
    :param return_code:
    :return:
    """
    locations: list[str] = []
    for d in server_block:
        dd = d['directive'].lower()
        if dd == 'location':
            da = d['args']
            db = d.get('block')
            if db and skip_on_return(db, return_code):
                continue
            special_comments = process_special_comments(db, hostname_var)
            location = prepare_location(da, special_comments)
            if location:
                locations.append(location)
            nested_locations = get_locations(db, hostname_var, return_code)
            if len(nested_locations):
                locations.extend(nested_locations)

    return locations


def process_servers(html_block: list, hostname_var, default_port=80, return_code=399, skip_locations=False) \
        -> list[dict[str, tuple[str]]]:
    """
    Обрабатывает html block crossplane.parse. возвращает список словарей в котором лежат server_name's & location's
    Не включаются в список, если return http code больше return_code
    Поддерживаются специальные комментарии:
        # replace: server_name = changed_server_name
        имя из списка будет заменено на другое
        # replace_all:
        вся строка с именами будет заменена на новую
        # skip_this: True
        пропустить этот сервер
        # var: $var_name = var_value
        # var: @another_var_name = var_value
        переменные встречающиеся в именах будут заменены в соответствии с вышеописанным списком
    Имена из директивы server_name, такие как:
          - *.example.org - по умолчанию будут заменены на www.example.org,
          - .example.org - будет заменено на example.org,
          - www.example.* - удаляется, т.к. невозможно точно предсказать какие имена в реальности будут использованы,
          - ~^www\..+\.example\.org$ - все регулярные выражения также будут удаляться.
          - "" - удаляется, если значение не является единственным в списке, в противном случае заменяется на $hostname
          - имена *, _, --, !@# и другие некорректные имена удаляются из списка
    :param skip_locations: не обрабатывать блоки locations
    :param html_block: html block from crossplane.parse
    :param default_port: default listen port
    :param hostname_var: variable $hostname
    :param return_code: если встречается директива return и код больше, чем указан, сервер пропускается
    :rtype: list[{
                'server_names': tuple[str],
                'locations': tuple[str],
                'listen': tuple[str]
                }]
    """
    ret_val = []
    for d in html_block:
        dd = d['directive'].lower()
        if dd == 'server':
            server_block = d['block']
            if skip_on_return(server_block, return_code):
                continue
            server_names = get_server_names(server_block, hostname_var)
            if server_names:
                server = {
                    'server_names': server_names,
                    'locations': get_locations(server_block, hostname_var, return_code) if not skip_locations else [],
                    'listens': get_all_listen_directives(server_block, default_port)
                }
                ret_val.append(server)
    return ret_val


def get_URLs_from_config(config_file_name: str, hostname_var: str, default_port: int = 80,
                         return_code: int = 399, skip_locations=False) -> Optional[list[str]]:
    # TODO: написать
    pl = crossplane.parse(config_file_name, comments=True, combine=True, ignore=('types', 'events',))
    config = pl['config'][0]['parsed']
    # looking for a directive http
    http_block = None
    for d in config:
        if d['directive'].lower() == 'http':
            http_block = d['block']
            break
    if http_block is None:
        # something wrong with config file
        return None
    res = process_servers(http_block, hostname_var, default_port, return_code, skip_locations)
    # servers0_answer = [{
    #         'locations': ['/hbz', '/equal', '/ifequal_not_check_regexpr', '/namedLocation/to/hbz_value'],
    #         'server_names': ('hbz.ru',),
    #         'listens': [(80, 'http')],
    #     }]
    urls: list[str] = []
    for server in res:
        for listen in server['listens']:
            for server_name in server['server_names']:
                server_name_url = listen[1] + '://' + server_name
                if listen not in ((80, 'http'), (443, 'https')):
                    server_name_url += str(listen[0])
                urls.append(server_name_url)
                if not skip_locations:
                    for location in server['locations']:
                        if location == '/':
                            continue
                        if len(location) >= 1 and location[0] != '/':
                            location = '/' + location
                        urls.append(server_name_url + location)
    return urls
