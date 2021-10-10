import validators
import re

if __name__ == '__main__':
    pat = re.compile(r'(^|:)(?P<port>\d+)$')
    while True:
        validate = input("Enter string: ")
        print(len(validate))
        res = pat.search(validate)
        print(res)
        if res:
            print(res.groups())
            print(res.group('port'))
    # print(tuple(pat.split('asdsad')))
    # for domain in ['www.haulmont.com', 'haulmont.dev', 'www.haulmont.dev', 'haulmont.tech', 'haulmont.com',
    #                'www.haulmont.tech',
    #                'haulmont.org', 'www.haulmont.org', 'haulmont.net', 'www.haulmont.net', 'haulmont-technology.ru',
    #                'www.haulmont-technology.ru', 'haulmont-technology.com', 'www.haulmont-technology.com',
    #                'haulmont.co.uk',
    #                'www.haulmont.co.uk', 'haulmont-technology.co.uk', 'www.haulmont-technology.co.uk']:
    #     result = validators.domain(domain)
    #     if result:
    #         print('validated')
    #     else:
    #         print('not validated')
