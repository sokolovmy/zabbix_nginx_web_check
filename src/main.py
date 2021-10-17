#import validators
#import re
import dns.resolver

if __name__ == '__main__':
    # pat = re.compile(r'(^|:)(?P<port>\d+)$')
    while True:
        validate = input("Enter string: ")
        try:
            res = dns.resolver.resolve(validate)
            print(res.response)
        except Exception as e:
            print(e)
        #print(int(validate))
        # print(len(validate))
        # res = pat.search(validate)
        # print(res)
        # if res:
        #     print(res.groups())
        #     print(res.group('port'))
    # print(tuple(pat.split('asdsad')))
    # for domain in ['www.company.com', 'company.dev', 'www.company.dev', 'company.tech', 'company.com',
    #                'www.company.tech',
    #                'company.org', 'www.company.org', 'company.net', 'www.company.net', 'company-technology.ru',
    #                'www.company-technology.ru', 'company-technology.com', 'www.company-technology.com',
    #                'company.co.uk',
    #                'www.company.co.uk', 'company-technology.co.uk', 'www.company-technology.co.uk']:
    #     result = validators.domain(domain)
    #     if result:
    #         print('validated')
    #     else:
    #         print('not validated')
