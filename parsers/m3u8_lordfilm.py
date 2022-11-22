import json
import sys
import time

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# https://10rd-54.lordfilm6.zone
# https://211122.lordserial.click
# https://movie-2022.lordfilm6.zone
# https://lf20.lordfilm.lu

args = sys.argv[1:]
if len(args) == 0:
    sys.exit('укажите ссылку на страницу с фильмом/сериалом')

src_page = str(args[0]).strip()
if src_page == '':
    sys.exit('укажите ссылку на страницу с фильмом/сериалом')

src_page_url = urlparse(src_page)
if src_page_url is None or src_page_url.hostname == '':
    sys.exit('указана неправильная ссылка на страницу фильма/сериала')

headers = {
    'User-Agent': 'Mozilla/5.0 (Web0S; Linux/SmartTV) AppleWebKit/537.36 (KHTML, like Gecko) Chr0me/38.0.2125.122 Safari/537.36 LG Browser/8.00.00(LGE; 43UJ6307-ZA; 04.71.00; 1; DTV_W17P); webOS.TV-2017; LG NetCast.TV-2013 Compatible (LGE, 43UJ6307-ZA, wired)',
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-length': '0',
    'content-type': 'application/x-www-form-urlencoded',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}

sess = requests.session()
try:
    resp_main = sess.get(src_page, headers=headers)
except Exception as e:
    sys.exit(e)

if resp_main.status_code != 200:
    sys.exit(resp_main.text)

soup = BeautifulSoup(resp_main.text, 'lxml')

iframe = soup.find('iframe')
if iframe is None:
    sys.exit('не найден iframe')

iframe_attrs_src = iframe.attrs.get('src')
if iframe_attrs_src is None or iframe_attrs_src == '':
    sys.exit('не найден источник в iframe')

iframe_src = urlparse(iframe_attrs_src)
if iframe_src is None or iframe_src.hostname == '':
    sys.exit('неправильная ссылка в атрибуте iframe')

headers['sec-fetch-dest'] = 'iframe'
headers['sec-fetch-mode'] = 'navigate'
headers['sec-fetch-site'] = 'cross-site'
headers['upgrade-insecure-requests'] = '1'
headers['referer'] = f'{src_page_url.scheme}://{src_page_url.hostname}/'

try:
    response_script = sess.get(iframe_attrs_src, headers=headers)
except Exception as e:
    sys.exit(e)

if response_script.status_code != 200:
    sys.exit(response_script.content)

iframe_soup = BeautifulSoup(response_script.text, 'lxml')
scripts = iframe_soup.findAll('script')
if scripts is None or len(scripts) == 0:
    sys.exit('тег со скриптом инициализации плеере не найден')

for scr in scripts:
    content = str(scr.text).strip()
    if 'playerConfigs' in content:
        for content_line in content.split('\n'):
            if 'playerConfigs' in content_line:
                conf_str = content_line.replace('let playerConfigs =', '')
                conf_str = conf_str.replace(';', '')
                conf_str = conf_str.strip()
                try:
                    player = json.loads(conf_str)
                except Exception as e:
                    sys.exit(e)
                break

    elif content.startswith('var player'):
        content = content.replace('var player = new HDVBPlayer(', '')
        content = content.replace(');', '')
        try:
            player = json.loads(content)
        except Exception as e:
            sys.exit(e)

if player is None:
    sys.exit('не удалось инициализировать объект с данными из js-скрипта')

origin = f'{iframe_src.scheme}://{iframe_src.hostname}/'
referer = iframe_attrs_src
csrf = player.get('key')

headers = {
    'User-Agent': 'Mozilla/5.0 (Web0S; Linux/SmartTV) AppleWebKit/537.36 (KHTML, like Gecko) Chr0me/38.0.2125.122 Safari/537.36 LG Browser/8.00.00(LGE; 43UJ6307-ZA; 04.71.00; 1; DTV_W17P); webOS.TV-2017; LG NetCast.TV-2013 Compatible (LGE, 43UJ6307-ZA, wired)',
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-length': '0',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': origin,
    'referer': referer,
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'x-csrf-token': csrf,
}

path_file = str(player.get('file', ''))
if path_file == '':
    sys.exit('не удалось получить ссылку на файл для запросу плейлиста')

if path_file.startswith('/'):
    path_file = path_file[1:]

if path_file.startswith('~'):
    path_file = path_file[1:]

if not path_file.startswith('playlist/'):
    path_file = 'playlist/' + path_file

if not path_file.endswith('.txt'):
    path_file = path_file + '.txt'

settings_url = f'{iframe_src.scheme}://{iframe_src.hostname}/{path_file}'

try:
    response_settings = sess.post(settings_url, headers=headers)
except Exception as e:
    sys.exit(e)

if response_settings.status_code != 200:
    sys.exit(response_settings.content)

if response_settings.text.startswith('http'):
    print(response_settings.text)
    sys.exit(0)

try:
    response_settings_obj = response_settings.json()
except Exception as e:
    sys.exit(e)

if response_settings_obj is None:
    sys.exit('не удалось получить меню настроек фильма/сериала')

for resp in response_settings.json():
    # Сезоны
    sezon = resp.get('title')
    for folder in resp.get('folder'):
        # Серии
        epizode = folder.get('title')
        for tr_folder in folder.get('folder'):
            if len(tr_folder) > 0:
                _file = tr_folder.get('file')
                _url = f'{iframe_src.scheme}://{iframe_src.hostname}/playlist/{_file}.txt'
                print(f'{sezon} {epizode} Перевод: {tr_folder.get("title")}')
                r = requests.get(_url, headers=headers)
                if r.status_code != 200:
                    print(r.content)
                    time.sleep(3)
                    continue
                print(r.text)
                time.sleep(3)
