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
             'www.company.com', 'company.dev',
             'www.company.dev', 'company.tech',
             'company.com', 'www.company.tech',
             'company.org', 'www.company.org',
             'company.net', 'www.company.net',
             'company-technology.ru',
             'www.company-technology.ru',
             'company-technology.com',
             'www.company-technology.com',
             'company.co.uk', 'www.company.co.uk',
             'company-technology.co.uk',
             'www.company-technology.co.uk'
         ]
         },
        {'directive': 'return', 'line': 17, 'args': ['301', 'https://www.company.com$request_uri']}
    ],
    [
        {'directive': 'listen', 'line': 21, 'args': ['443', 'ssl', 'http2']},
        {'directive': 'server_name', 'line': 22, 'args': ['company.com']},
        {'directive': 'return', 'line': 23, 'args': ['301', 'https://www.company.com$request_uri']}
    ],
    [
        {'directive': 'listen', 'line': 27, 'args': ['443', 'ssl', 'http2']},
        {'directive': 'server_name', 'line': 28, 'args': ['company.dev', 'www.company.dev']},
        {'directive': 'return', 'line': 29, 'args': ['301', 'https://www.company.com$request_uri']}
    ],
    [
        {'directive': 'server_name', 'line': 33, 'args': ['www.company.com']},
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
        {'directive': 'server_name', 'line': 47, 'args': ['www.company.ru', 'company.ru']},
        {'directive': 'return', 'line': 48, 'args': ['301', 'https://www.company.ru$request_uri']}
    ],
    [
        {'directive': 'listen', 'line': 52, 'args': ['443', 'ssl', 'http2']},
        {'directive': 'server_name', 'line': 53, 'args': ['company.ru']},
        {'directive': 'return', 'line': 54, 'args': ['301', 'https://www.company.ru$request_uri']}
    ],
    [
        {'directive': 'server_name', 'line': 57, 'args': ['www.company.ru']},
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

servers2 = [[{'args': ['test.ru', 'www.test.*', '', '_', '*', '*.exmaple.net'],
              'directive': 'server_name',
              'line': 4},
             {'args': [],
              'comment': ' replace: www.test.* = www.test.ru',
              'directive': '#',
              'line': 5},
             {'args': [], 'comment': ' replace_all: hbz.ru', 'directive': '#', 'line': 6},
             {'args': [],
              'comment': ' var: $hbz_var = hbz_value',
              'directive': '#',
              'line': 7},
             {'args': ['1.1.1.1:80'], 'directive': 'listen', 'line': 8},
             {'args': ['/hbz'], 'block': [], 'directive': 'location', 'line': 9},
             {'args': ['=', '/equal'], 'block': [], 'directive': 'location', 'line': 11},
             {'args': ['~', '/regexpr'], 'block': [], 'directive': 'location', 'line': 13},
             {'args': ['~*', '/CaseInsentiveRegexpr'],
              'block': [],
              'directive': 'location',
              'line': 15},
             {'args': ['^~', '/ifequal_not_check_regexpr'],
              'block': [],
              'directive': 'location',
              'line': 17},
             {'args': ['@NamedLocatoin'],
              'block': [],
              'directive': 'location',
              'line': 19}]]
