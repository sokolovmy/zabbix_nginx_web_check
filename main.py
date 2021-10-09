import validators

if __name__ == '__main__':
    for domain in ['www.haulmont.com', 'haulmont.dev', 'www.haulmont.dev', 'haulmont.tech', 'haulmont.com',
                   'www.haulmont.tech',
                   'haulmont.org', 'www.haulmont.org', 'haulmont.net', 'www.haulmont.net', 'haulmont-technology.ru',
                   'www.haulmont-technology.ru', 'haulmont-technology.com', 'www.haulmont-technology.com',
                   'haulmont.co.uk',
                   'www.haulmont.co.uk', 'haulmont-technology.co.uk', 'www.haulmont-technology.co.uk']:
        result = validators.domain(domain)
        if result:
            print('validated')
        else:
            print('not validated')
