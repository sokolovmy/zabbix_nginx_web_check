import re
import validators

def process_special_comments(dictionary: dict) -> dict:
    """
    Обрабатывает комментарии и ищет специальные, по ним составляет словарь
    Примеры специальных комментариев:
        # replace: <changed_name> = <list of changed names through a space>
        # replace_all: <list of changed names through a space>
        # var: $<name_of_var = <value_of_var>
        # skip_this: True
    :rtype: dictionary
    :param dictionary:  - список директив в {}
    """
    res = {
        'replace': {},
        'var': {},
        # 'replace_all': str - appear if it's founded
        # 'skip_this': True - appear if it's founded
    }
    patt = re.compile(r"^\s*([^:]+):\s+(.+)$")
    patt_eq = re.compile(r"^\s*(.+)\s+=\s+(.+)$")
    patt_split = re.compile((r"[\s,]+"))
    for i in dictionary:
        directive = i.get('directive')
        if directive and directive == '#':
            comment = i.get('comment')
            m = patt.match(comment)
            if m:
                cmd, cmd_val = m.group(1, 2)
                if cmd == 'skip_this' and cmd_val == 'True':
                    res['skip_this'] = True
                if cmd == 'replace_all':
                    res['replace_all'] = cmd_val
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


def get_server_names(server: dict, special_comments: dict = None) -> tuple[str]:
    """
        check server_name directive & return tuple of server names

        Имена из директивы server_name, такие как:
            - *.example.org - по умолчанию будут заменены на www.example.org,
            - .example.org - будет заменено на example.org,
            - www.example.* - удаляется, т.к. невозможно точно предсказать какие имена в реальности будут использованы,
            - ~^www\..+\.example\.org$ - все регулярные выражения также будут удаляться.
            - "" - удаляется, если значение не является едиственным в списке, в противном случае заменяется на $hostname
            - имена *, _, --, !@# и другие некорректные имена удаляются из списка
            $hostname
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

        Примеры
        # replace: *.example.org = mysite_name.example.org another_site_name.example.org etc.example.org`
        # replace: .example.org = www.example.org
        # replace_all: www.example.org
        # var: $Host = mysite.domain.com
        # var $Hostname = anothermysitename.domain.com

    :param server:
    """
    for i in server:
        d = i.get('directive')
        if d and d == 'server_name':  args = i['args']
        if args:
            server_names = []
            if special_comments is None: special_comments = process_special_comments(i)
            for server_name in server_names:
                if validators.domain(server_name):
                    pass
                else:
                    pass

    pass


if __name__ == '__main__':
    get_server_names()
