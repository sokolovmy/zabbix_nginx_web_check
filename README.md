Zabbix LLD autodiscovery URLs From Nginx Config.
===
 Скрипт *znwcagent.py* парсит конфигурационный файл nginx.conf. 
 Устанавливается на наблюдаемый хост.

Скрипт *znwcserver.py* проверяет передаваемый ему URL. Возвращает
некоторое количество числовых метрик. В случае проблем с 
мониторингом ресурса возвращает коды ошибки.
Устанавливается на zabbix сервер в качестве скрипта внешних проверок.

Шаблон *znwc.xml* необходимо импортировать в zabbix.
Подключить к наблюдаемому хосту.

# *znwcagent.py*

Пример обрабатываемого конфигурационного файла:
    
    html {
        server {
            listen 443 ssl default_server;
            listen 80;
            listen 1.1.1.1:80;
            listen [::]:8080;

            ssl on;

            server_name .company.name *.company.com www.company.* $host.$domain '';

            # replace: server_name = changed_server_name[, another_server_name[, ...]]
            # replace_all: changed_name[, another_changed_name[, ...]]
            # skip_this: True
            # var: $var_name = var_value
            # var: @another_var_name = var_value
            
            return 301 https://another.server.name/

            location /some/one/location {
                # replace_all: /other/location
                # skip_this: True
                # var: $var_name = var_value
                # var: @another_var_name = var_value
                return 301 https://another.server.name/location
            }
        }
    }

Имена из директивы server_name, такие как:
* `*.example.org` - по умолчанию будут заменены на `www.example.org`,
* `.example.org` - будет заменено на `example.org`,
* `www.example.*` - удаляется, т.к. невозможно точно предсказать какие имена в реальности будут использованы,
* `~^www\..+\.example\.org$` или `~*WWW\..+\.com$` - все регулярные выражения также будут удаляться.
* `""` - удаляется, если значение не является единственным в списке, в противном случае заменяется на `$hostname`
* имена `*`, `_`, `--`, `!@#` и другие некорректные имена удаляются из списка
Любое имя, в том числе некорректное, может быть заменено с помощью специальных комментариев.
Поддерживаются специальные комментарии:

    
    # replace: server_name = changed_server_name[, another_server_name[, ...]]
    # имя из списка будет заменено на другое. Имена проверяются на корректность.
    # replace_all: changed_name[, another_changed_name[, ...]]
    # вся строка с именами будет заменена на новую. Проверка на корректность не производится
    # skip_this: True
    # пропустить этот сервер
    # var: $var_name = var_value
    # var: @another_var_name = var_value
    # Переменные встречающиеся в именах будут заменены в соответствии с вышеописанным списком

    

Аргументы командной строки:

     usage: znwcagent.py [-h] [--version] [-u] [-s] [-r <ret code>] [-p <port>]
                        [-H <hostname>] [-n]
                        [<config file name>]
    
    Get URLs from nginx config file
    
    positional arguments:
      <config file name>    Path to the nginx config file. default:
                            /etc/nginx/nginx.conf
    
    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      -u, --human           Human friendly output format
      -s, --skip_location   Add this key if you don't want to handle locations
      -r <ret code>, --ret-code <ret code>
                            Return code. All server and location directives, if
                            they contain return <code>, will not be processed if
                            <code> is greater than <ret code>. Default = 399
      -p <port>, --port <port>
                            Specify the default port for server directives for
                            which there is no listen directive. Default value = 80
      -H <hostname>, --hostname <hostname>
                            Specify the hostname. Default is LAPTOP-E0P7TO1G
      -n, --check-dns       Do Check dns records for names in server_name
                            directive

 # *znwcserver.py*

Возвращает ошибки соединения:
* `0` - `нет ошибки`, соединение с сервером было установлено
* `1` - `HTTP Error`
* `2` - `SSL Error`
* `3` - `Connect Timeout`
* `4` - `Read Timeout`
* `5` - `Connection Error`
* `6` - `Too Many Redirects`
* `7` - `Missing Schema`
* `8` - `Invalid URL`
* `9` - `Invalid Header`
* `1000` - `Unknown Error`

Если ошибок соединения нет, возвращает `HTTP ответ сервера` 
на запрашиваемый URL и `время отклика` запрашиваемого ресурса.
По времени отклика можно строить графики

# *znwc.xml*

Шаблон для Zabbix сервера, прикрепляется к хосту на котором сконфигурирован
*znwcagent.py*

Макросы используемые в шаблоне:

