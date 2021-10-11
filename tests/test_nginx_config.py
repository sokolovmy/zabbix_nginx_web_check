from unittest import TestCase

from nginx_config import process_special_comments, get_server_names, get_listen, prepare_location, skip_on_return, \
    get_locations, process_servers, get_URLs_from_config


class TestNginxConfig(TestCase):
    def setUp(self) -> None:
        self.dir_server_comments = [
            {'directive': '#', 'comment': 'replace: www.test.* = www.test.ru'},
            {'directive': '#', 'comment': 'replace: multi.example.org = www.test.ru test.ru'},
            {'directive': '#', 'comment': 'replace: ~^www\..+\.example\.org$ = www.test.example.org'},
            {'directive': '#', 'comment': 'var: $hbz_var = hbz_value'},
            {'directive': '#', 'comment': 'var: $hostname = herov.domain.com'},
            {'directive': 'location', 'args': '/', 'block': {}},
        ]
        self.test_comments_result = {
            'replace': {
                'www.test.*': ('www.test.ru',),
                '~^www\..+\.example\.org$': ('www.test.example.org',),
                'multi.example.org': ('www.test.ru', 'test.ru',)
            },
            'var': {
                '$hbz_var': 'hbz_value',
                '$hostname': 'herov.domain.com',
            }
        }
        self.dir_server_comments_replace_all = [
                                                   {'directive': '#', 'comment': 'replace_all: hbz.ru'},
                                               ] + self.dir_server_comments

        self.test_comments_result_replace_all = {
                                                    'replace_all': ('hbz.ru',),
                                                } | self.test_comments_result

        self.dir_server_comments_skip_this = [
                                                 {'directive': '#', 'comment': ' skip_this: True'},
                                             ] + self.dir_server_comments

        self.test_comments_result_skip_this = {
                                                  'skip_this': True,
                                              } | self.test_comments_result

    def test_process_special_comments(self):
        self.assertEqual(
            self.test_comments_result,
            process_special_comments(self.dir_server_comments, 'test.hostname.org'),
            'without skip_this:'
        )

    def test_process_special_comments_with_skip_this(self):
        self.assertEqual(
            self.test_comments_result_skip_this,
            process_special_comments(self.dir_server_comments_skip_this, 'test.hostname.org'),
            'with skip_this:'
        )

    def test_process_special_comments_with_replace_all(self):
        self.assertEqual(
            self.test_comments_result_replace_all,
            process_special_comments(self.dir_server_comments_replace_all, 'test.hostname.org'),
            'with replace_all:'
        )

    def test_get_server_names_single_start_dot(self):
        self.assertEqual(
            ('example.ru',),
            get_server_names([{'directive': 'server_name', 'args': ['.example.ru']}], ''),
        )

    def test_get_server_names_single_empty_name(self):
        self.assertEqual(
            ('test.hostname.org',),
            get_server_names([{'directive': 'server_name', 'args': ['']}], 'test.hostname.org'),
        )

    def test_get_server_names_single_empty_name2(self):
        self.assertEqual(
            ('h.domain.com',),
            get_server_names(
                [
                    {'directive': 'server_name', 'args': ['']},
                    {'directive': '#', 'comment': 'var: $hostname = h.domain.com'}
                ],
                'test.hostname.org'
            ),
        )

    def test_get_server_names_single_empty_name3(self):
        self.assertEqual(
            ('t.hostname.org',),
            get_server_names([], 't.hostname.org'),
        )

    def test_get_server_names(self):
        self.assertEqual(
            ('test.ru', 'www.example.net'),
            get_server_names(
                [
                    {'directive': 'server_name', 'args': ['test.ru', 'www.test.*', '', '_', '*', '*.example.net']}
                ] + self.dir_server_comments,
                'test.hostname.org'),
        )

    def test_get_server_names_skip_this(self):
        self.assertEqual(
            None,
            get_server_names(
                [
                    {'directive': 'server_name', 'args': ['test.ru', 'www.test.*', '', '_', '*', '*.example.net']}
                ] + self.dir_server_comments_skip_this,
                'test.hostname.org'),
        )

    def test_get_server_names_replace_all(self):
        self.assertEqual(
            ('hbz.ru',),
            get_server_names(
                [
                    {'directive': 'server_name', 'args': ['test.ru', 'www.test.*', '', '_', '*', '*.example.net']}
                ] + self.dir_server_comments_replace_all,
                'test.hostname.org'),
        )

    def test_get_server_names_vars(self):
        self.assertEqual(
            ('test.hbz_value', 'www.example.net'),
            get_server_names(
                [
                    {'directive': 'server_name', 'args': ['test.$hbz_var', 'www.test.*', '', '_', '*', '*.example.net']}
                ] + self.dir_server_comments,
                'test.hostname.org'),
        )

    def test_get_listen(self):
        checks = {
            (70, 'http',): ['1.1.1.1:70'],
            (80, 'http',): ['1.2.3.4'],
            (90, 'http',): ['[::]:90'],
            (80, 'http',): ['[::1]'],
            (80, 'http',): ['*'],
            (90, 'http'): ['90', 'so_keepalive=on 1:2:3'],
            (80, 'http',): ['hbz.ru'],
            (8090, 'http',): ['hbz.ru:8090'],
            (8080, 'http',): ['8080'],
            (443, 'https'): ['443', 'ssl'],
            (443, 'https'): ['1.2.3.4:443', 'ssl'],
            (443, 'https'): ['hbz.ru:443', 'ssl']
        }
        for answer in checks:
            self.assertEqual(
                answer,
                get_listen(checks[answer])
            )

    def test_prepare_location_replace_all(self):
        self.assertEqual(
            '/replaced',
            prepare_location(['/'], {'replace_all': ('/replaced',)})
        )

    def test_prepare_location_skip_this(self):
        self.assertEqual(
            None,
            prepare_location(['/'], {'skip_this': True})
        )

    def test_prepare_location_non_corrected_comment(self):
        self.assertEqual(
            '/',
            prepare_location(
                ['/'],
                {
                    'replace': {'/': '/replaced'},
                    'var': {}
                }
            )
        )

    def test_prepare_location_check_unsupported(self):
        self.assertEqual(
            None,
            prepare_location(['~\kjhguyt$'], {})
        )
        self.assertEqual(
            None,
            prepare_location(['~*jytrhfljhg'], {})
        )
        self.assertEqual(
            None,
            prepare_location(['~', '/'], {})
        )
        self.assertEqual(
            None,
            prepare_location(['~*', '/'], {})
        )
        self.assertEqual(
            None,
            prepare_location(['@named'], {'var': {}})
        )
        self.assertEqual(
            None,
            prepare_location(['=', '@named'], {})
        )

    def test_prepare_location_supported(self):
        comments = {'var': {}}
        self.assertEqual(
            '/location',
            prepare_location(['=', '/location'], comments)
        )
        self.assertEqual(
            '/location2',
            prepare_location(['^~', '/location2'], {})
        )
        self.assertEqual(
            '/location3',
            prepare_location(['/location3'], {})
        )
        self.assertEqual(
            '/location4',
            prepare_location(['=/location4'], comments)
        )
        self.assertEqual(
            '/location5',
            prepare_location(['^~/location5'], {})
        )

    def test_prepare_location_var(self):
        comments = {'var': {'@named': '/change_named_location', '$hbz_var': '/hbz'}}
        self.assertEqual(
            '/location',
            prepare_location(['=', '/location'], comments)
        )
        self.assertEqual(
            '/change_named_location',
            prepare_location(['^~', '@named'], comments)
        )
        self.assertEqual(
            '/loc/hbz',
            prepare_location(['/loc$hbz_var'], comments)
        )

    def test_prepare_empty_loc(self):
        self.assertEqual(
            None,
            prepare_location([''], {})
        )

    def test_skip_on_return(self):
        self.assertEqual(
            True,
            skip_on_return([{'directive': 'return', 'args': ['301', 'http://her.znama.kuda']}], 299)
        )
        self.assertEqual(
            False,
            skip_on_return([{'directive': 'return', 'args': ['301', 'http://her.znama.kuda']}], 301)
        )
        self.assertEqual(
            True,
            skip_on_return([{'directive': 'return', 'args': ['502']}], 399)
        )
        self.assertEqual(
            False,
            skip_on_return([{'directive': 'return', 'args': ['50w2']}], 399)
        )
        self.assertEqual(
            False,
            skip_on_return([{'directive': 'listen', 'args': ['80']}], 399)
        )

    def test_get_locations(self):
        self.assertEqual(
            ['/var/asdf/my.host.name', '/named_location', '/', '/hbz', '/hbz/hbz', '/1/2/4'],
            get_locations([
                {'directive': 'location', 'args': ['/var/$qwe$hostname'], 'block': [
                    {'directive': '#', 'comment': ' var: $qwe = asdf/'}
                ]},
                {'directive': 'location', 'args': ['skipped'], 'block': [
                    {'directive': '#', 'comment': ' skip_this: True'}
                ]},
                {'directive': 'location', 'args': ['@named'], 'block': [
                    {'directive': '#', 'comment': ' replace_all: /named_location'}
                ]},
                {'directive': 'location', 'args': ['/'], 'block': []},
                {'directive': 'location', 'args': ['/hbz'], 'block': [
                    {'directive': 'location', 'args': ['/hbz/hbz'], 'block': []},
                    {'directive': 'location', 'args': ['/hbz/gubz'], 'block': [
                        {'directive': 'return', 'args': ['400']}
                    ]}
                ]},
                {'directive': 'location', 'args': ['/1/2/3'], 'block': [
                    {'directive': 'return', 'args': ['500']},
                ]},
                {'directive': 'location', 'args': ['/1/2/4'], 'block': [
                    {'directive': 'return', 'args': ['250']},
                ]},
            ], 'my.host.name')
        )

    def test_process_server(self):
        self.assertEqual(
            servers_answer,
            process_servers(servers, hostname_var='host.domain.name')
        )

    def test_process_server0(self):
        self.assertEqual(
            servers0_answer,
            process_servers(servers0, hostname_var='host.domain.name')
        )

    def test_get_urls_from_config(self):
        self.assertEqual(
            config_res,
            get_URLs_from_config('./nginx.conf', 'h.domain.com')
        )

    def test_get_urls_file_not_found(self):
        self.assertEqual(
            None,
            get_URLs_from_config('nonexistent.conf', 'h.domain.com')
        )

    def test_get_urls_file_config2(self):
        self.assertEqual(
            config_res2,
            get_URLs_from_config('nginx2.conf', 'h.domain.com')
        )

    def test_get_urls_file_config3(self):
        self.assertEqual(
            ['http://hbz.ru',
             'http://hbz.ru/hbz',
             'http://hbz.ru/equal',
             'http://hbz.ru/ifequal_not_check_regexpr',
             'https://www.haulmont.com',
             'https://www.haulmont.com/forms',
             'https://www.haulmont.ru',
             'https://www.haulmont.ru/sites/default/files/webform/cv-ru'],
            get_URLs_from_config('nginx2.conf', 'h.domain.com', 80, 300)
        )

    def test_get_urls_file_config4(self):
        self.assertEqual(
            ['http://hbz.ru', 'https://www.haulmont.com', 'https://www.haulmont.ru'],
            get_URLs_from_config('nginx2.conf', 'h.domain.com', 80, 300, True)
        )


config_res = ['http://hbz.ru',
              'http://hbz.ru/hbz',
              'http://hbz.ru/equal',
              'http://hbz.ru/ifequal_not_check_regexpr',
              'http://non.standard.port:1234',
              'http://non.standard.port:1234/noncorrect/asd']

config_res2 = ['http://hbz.ru',
               'http://hbz.ru/hbz',
               'http://hbz.ru/equal',
               'http://hbz.ru/ifequal_not_check_regexpr',
               'http://www.haulmont.com',
               'http://haulmont.dev',
               'http://www.haulmont.dev',
               'http://haulmont.tech',
               'http://haulmont.com',
               'http://www.haulmont.tech',
               'http://haulmont.org',
               'http://www.haulmont.org',
               'http://haulmont.net',
               'http://www.haulmont.net',
               'http://haulmont-technology.ru',
               'http://www.haulmont-technology.ru',
               'http://haulmont-technology.com',
               'http://www.haulmont-technology.com',
               'http://haulmont.co.uk',
               'http://www.haulmont.co.uk',
               'http://haulmont-technology.co.uk',
               'http://www.haulmont-technology.co.uk',
               'https://haulmont.com',
               'https://haulmont.dev',
               'https://www.haulmont.dev',
               'https://www.haulmont.com',
               'https://www.haulmont.com/forms',
               'http://www.haulmont.ru',
               'http://haulmont.ru',
               'https://haulmont.ru',
               'https://www.haulmont.ru',
               'https://www.haulmont.ru/sites/default/files/webform/cv-ru']

servers0_answer = [
    {
        'locations': ['/', 'incorrect_location/', '/hbz', '/equal', '/ifequal_not_check_regexpr',
                      '/namedLocation/to/hbz_value'],
        'server_names': ('hbz.ru',),
        'listens': [(80, 'http')],
    }
]
servers0 = [
    {'directive': 'server', 'block': [
        {'args': ['test.ru', 'www.test.*', '', '_', '*', '*.exmaple.net'], 'directive': 'server_name', 'line': 4},
        {'args': [], 'comment': ' replace: www.test.* = www.test.ru', 'directive': '#', 'line': 5},
        {'args': [], 'comment': ' replace_all: hbz.ru', 'directive': '#', 'line': 6},
        {'args': [], 'comment': ' var: $hbz_var = hbz_value', 'directive': '#', 'line': 7},
        {'args': ['1.1.1.1:80'], 'directive': 'listen', 'line': 8},
        {'args': ['/'], 'block': [], 'directive': 'location', 'line': 9},
        {'args': ['incorrect_location/'], 'block': [], 'directive': 'location', 'line': 9},
        {'args': ['/hbz'], 'block': [], 'directive': 'location', 'line': 9},
        {'args': ['=', '/equal'], 'block': [], 'directive': 'location', 'line': 11},
        {'args': ['~', '/regexpr'], 'block': [], 'directive': 'location', 'line': 13},
        {'args': ['~*', '/CaseInsentiveRegexpr'], 'block': [], 'directive': 'location', 'line': 15},
        {'args': ['^~', '/ifequal_not_check_regexpr'], 'block': [], 'directive': 'location', 'line': 17},
        {'args': ['@NamedLocation'], 'directive': 'location', 'line': 19, 'block': [
            {'comment': ' var: @NamedLocation = /namedLocation/to/hbz_value', 'directive': '#'},
        ]}
    ]},
    {'directive': 'server', 'block': [
        {'directive': 'server_name', 'args': ['skipped.server.com']},
        {'directive': 'return', 'args': ['500']}
    ]}
]

servers_answer = [
    {'listens': [(80, 'http')], 'locations': [], 'server_names': ('hbz.ru',)},
    {'listens': [(80, 'http')], 'locations': [],
     'server_names': (
         'www.haulmont.com', 'haulmont.dev', 'www.haulmont.dev', 'haulmont.tech', 'haulmont.com', 'www.haulmont.tech',
         'haulmont.org', 'www.haulmont.org', 'haulmont.net', 'www.haulmont.net', 'haulmont-technology.ru',
         'www.haulmont-technology.ru', 'haulmont-technology.com', 'www.haulmont-technology.com',
         'haulmont.co.uk', 'www.haulmont.co.uk', 'haulmont-technology.co.uk', 'www.haulmont-technology.co.uk'
     )},
    {'listens': [(443, 'https')], 'locations': [], 'server_names': ('haulmont.com',)},
    {'listens': [(443, 'https')], 'locations': [], 'server_names': ('haulmont.dev', 'www.haulmont.dev')},
    {'listens': [(443, 'https')], 'locations': ['/', '/forms'], 'server_names': ('www.haulmont.com',)},
    {'listens': [(80, 'http')], 'locations': [], 'server_names': ('www.haulmont.ru', 'haulmont.ru')},
    {'listens': [(443, 'https')], 'locations': [], 'server_names': ('haulmont.ru',)},
    {
        'listens': [(443, 'https')],
        'locations': ['/sites/default/files/webform/cv-ru', '/'],
        'server_names': ('www.haulmont.ru',)
    }
]

servers = [
    {'directive': 'server', 'block': [
        {'directive': 'server_name', 'line': 4, 'args': ['test.ru', 'www.test.*', '', '_', '*', '*.exmaple.net']},
        {'directive': '#', 'line': 5, 'args': [], 'comment': ' replace: www.test.* = www.test.ru'},
        {'directive': '#', 'line': 6, 'args': [], 'comment': ' replace_all: hbz.ru'},
        {'directive': '#', 'line': 7, 'args': [], 'comment': ' var: $hbz_var = hbz_value'},
        {'directive': 'listen', 'line': 8, 'args': ['1.1.1.1:80']}
    ]},
    {'directive': 'server', 'block': [
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
    ]},
    {'directive': 'server', 'block': [
        {'directive': 'listen', 'line': 21, 'args': ['443', 'ssl', 'http2']},
        {'directive': 'server_name', 'line': 22, 'args': ['haulmont.com']},
        {'directive': 'return', 'line': 23, 'args': ['301', 'https://www.haulmont.com$request_uri']}
    ]},
    {'directive': 'server', 'block': [
        {'directive': 'listen', 'line': 27, 'args': ['443', 'ssl', 'http2']},
        {'directive': 'server_name', 'line': 28, 'args': ['haulmont.dev', 'www.haulmont.dev']},
        {'directive': 'return', 'line': 29, 'args': ['301', 'https://www.haulmont.com$request_uri']}
    ]},
    {'directive': 'server', 'block': [
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
    ]},
    {'directive': 'server', 'block': [
        {'directive': 'listen', 'line': 46, 'args': ['80']},
        {'directive': 'server_name', 'line': 47, 'args': ['www.haulmont.ru', 'haulmont.ru']},
        {'directive': 'return', 'line': 48, 'args': ['301', 'https://www.haulmont.ru$request_uri']}
    ]},
    {'directive': 'server', 'block': [
        {'directive': 'listen', 'line': 52, 'args': ['443', 'ssl', 'http2']},
        {'directive': 'server_name', 'line': 53, 'args': ['haulmont.ru']},
        {'directive': 'return', 'line': 54, 'args': ['301', 'https://www.haulmont.ru$request_uri']}
    ]},
    {'directive': 'server', 'block': [
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
    ]}
]
