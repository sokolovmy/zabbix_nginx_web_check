from unittest import TestCase

from nginx_config import process_special_comments

servers = [
    [
        {'directive': 'server_name', 'line': 4, 'args': ['test.ru', 'www.test.*', '', '_', '*', '*.exmaple.net']},
        {'directive': '#', 'line': 5, 'args': [], 'comment': ' replace: www.test.* = www.test.ru'},
        {'directive': '#', 'line': 6, 'args': [], 'comment': ' replace_all: hbz.ru'},
        {'directive': '#', 'line': 7, 'args': [], 'comment': ' var: $hbz_var = hbz_value'},
        {'directive': 'listen', 'line': 8, 'args': ['1.1.1.1:80']}
    ],
    [
        {'directive': 'listen', 'line': 15, 'args': ['80']},
        {'directive': 'server_name', 'line': 16,
         'args': [
             'www.haulmont.com', 'haulmont.dev',
             'www.haulmont.dev', 'haulmont.tech',
             'haulmont.com', 'www.haulmont.tech',
             'haulmont.org', 'www.haulmont.org',
             'haulmont.net', 'www.haulmont.net',
             'haulmont-technology.ru',
             'www.haulmont-technology.ru',
             'haulmont-technology.com',
             'www.haulmont-technology.com',
             'haulmont.co.uk', 'www.haulmont.co.uk',
             'haulmont-technology.co.uk',
             'www.haulmont-technology.co.uk'
         ]
         },
        {'directive': 'return', 'line': 17, 'args': ['301', 'https://www.haulmont.com$request_uri']}
    ],
    [
        {'directive': 'listen', 'line': 21, 'args': ['443', 'ssl', 'http2']},
        {'directive': 'server_name', 'line': 22, 'args': ['haulmont.com']},
        {'directive': 'return', 'line': 23, 'args': ['301', 'https://www.haulmont.com$request_uri']}
    ],
    [
        {'directive': 'listen', 'line': 27, 'args': ['443', 'ssl', 'http2']},
        {'directive': 'server_name', 'line': 28, 'args': ['haulmont.dev', 'www.haulmont.dev']},
        {'directive': 'return', 'line': 29, 'args': ['301', 'https://www.haulmont.com$request_uri']}
    ],
    [
        {'directive': 'server_name', 'line': 33, 'args': ['www.haulmont.com']},
        {'directive': 'listen', 'line': 34, 'args': ['443', 'ssl', 'http2']},
        {
            'directive': 'location', 'line': 35, 'args': ['/'],
            'block': [{'directive': 'include', 'line': 36, 'args': ['./includes/proxy_pass_reverse'], 'includes': [1]},
                      {'directive': 'proxy_pass', 'line': 37, 'args': ['http://192.168.33.97:3002$request_uri']}]
        },
        {
            'directive': 'location', 'line': 40, 'args': ['/forms'],
            'block': [{'directive': 'proxy_set_header', 'line': 41, 'args': ['X-Real-IP', '$remote_addr']},
                      {'directive': 'proxy_pass', 'line': 42, 'args': ['http://192.168.33.97:3003']}]
        },
    ],
    [
        {'directive': 'listen', 'line': 46, 'args': ['80']},
        {'directive': 'server_name', 'line': 47, 'args': ['www.haulmont.ru', 'haulmont.ru']},
        {'directive': 'return', 'line': 48, 'args': ['301', 'https://www.haulmont.ru$request_uri']}
    ],
    [
        {'directive': 'listen', 'line': 52, 'args': ['443', 'ssl', 'http2']},
        {'directive': 'server_name', 'line': 53, 'args': ['haulmont.ru']},
        {'directive': 'return', 'line': 54, 'args': ['301', 'https://www.haulmont.ru$request_uri']}
    ],
    [
        {'directive': 'server_name', 'line': 57, 'args': ['www.haulmont.ru']},
        {'directive': 'listen', 'line': 59, 'args': ['443', 'ssl', 'http2']},
        {
            'directive': 'location', 'line': 60, 'args': ['~*cv-ru\\/.*xml$'],
            'block': [{'directive': 'return', 'line': 61, 'args': ['520']}]
        },
        {
            'directive': 'location', 'line': 63, 'args': ['~*\\?q=node\\/add*$'],
            'block': [{'directive': 'return', 'line': 64, 'args': ['520']}]},
        {
            'directive': 'location', 'line': 67,
            'args': ['/sites/default/files/webform/cv-ru'],
            'block': [
                {'directive': 'proxy_pass', 'line': 68,
                 'args': ['http://192.168.33.68/sites/default/files/webform/cv-ru']}
            ]
        },
        {
            'directive': 'location', 'line': 70, 'args': ['/'],
            'block': [{'directive': 'proxy_pass', 'line': 71, 'args': ['http://192.168.33.68/']}]}
    ]
]


class TestNginxConfig(TestCase):
    self.test_comments_dict = [

        {'directive': '#', 'comment': 'replace: www.test.* = www.test.ru'},
        {'directive': '#', 'comment': 'replace: ~^www\..+\.example\.org$ = www.test.example.org'},
        {'directive': '#', 'comment': 'replace_all: hbz.ru'},
        {'directive': '#', 'comment': 'var: $hbz_var = hbz_value'},
        {'directive': '#', 'comment': 'var: $Hostname = herov.domain.com'},
        {'directive': '#', 'comment': ' skip_this: True'},
        {'directive': 'location', 'args': '/', 'block': {}},
    ]
    def setUp(self) -> None:
        self.test_comments_result = {
            'replace_all': 'hbz.ru',
            'skip_this': True,
            'replace': {
                'www.test.*': 'www.test.ru',
                '~^www\..+\.example\.org$': 'www.test.example.org'

            },
            'var': {
                '$hbz_var': 'hbz_value',
                '$Hostname': 'herov.domain.com',
            }
        }

    def test_process_special_comments(self):
        self.assertEqual(process_special_comments(self.test_comments_dict), self.test_comments_result)
