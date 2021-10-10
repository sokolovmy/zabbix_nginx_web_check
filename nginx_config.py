import re
from typing import Optional, Any

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
        'replace': {},
        # TODO: set replace to (str, tuple[str, ...]),
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
                    replace: (str, tuple[str, ...]) = res['replace']
                    m = patt_eq.match(cmd_val)
                    if m:
                        key = m.group(1)
                        val = m.group(2)
                        replace[key] = tuple(patt_split.split(val))
                elif cmd == 'var':
                    m = patt_eq.match(cmd_val)
                    if m:
                        key, val = m.group(1, 2)
                        res['var'][key] = val
    return res


def get_server_names(server: list, hostname_var: str, special_comments: dict = None) -> Optional[tuple[str, ...]]:
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
        # replace: *.example.org = mysite_name.example.org another_site_name.example.org etc.example.org`
        # replace: .example.org = www.example.org
        # replace_all: www.example.org
        # var: $Host = mysite.domain.com
        # var $Hostname = anothermysitename.domain.com

    :param server: словарь возвращаемый crossplane.parse из директивы server
    :param special_comments: словарь подготовленный process_special_comments
    :param hostname_var: $hostname
    """
    def prep_name_var(name: str) -> str:

        vars = special_comments['var']
        for var in vars:
            name = name.replace(var, vars[var])
        return name

    def prep_name(name: str, single=False) -> Optional[str]:
        res = special_comments.get(name)
        if res is None:
            name = prep_name_var(name)
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

    server_names = []
    if special_comments is None:
        special_comments = process_special_comments(server, hostname_var)

    if special_comments.get('skip_this'):
        return None
    elif special_comments.get('replace_all'):
        return special_comments['replace_all']

    for i in server:
        d = i.get('directive')
        if d and d == 'server_name':
            args = i['args']
            if args:
                single = len(args) == 1
                for arg in args:
                    server_name = prep_name(arg, single)
                    if server_name:
                        server_names.append(server_name)
    if len(server_names):
        return tuple(server_names)
    else:
        return None
