from unittest import TestCase

from nginx_config import process_special_comments, get_server_names, get_listen, prepare_location


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
