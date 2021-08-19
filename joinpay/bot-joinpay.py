import csv
import hashlib
import json
import os
import re
from datetime import datetime, timedelta

import aiohttp
import urllib3
import yaml
import asyncio
import sys

from aiogram import Bot, Dispatcher, types
from bs4 import BeautifulSoup
from yarl import URL

CFG_PATH = 'config-bot-joinpay.yml'

CFG = {}

storage = {}

urllib3.disable_warnings()

fieldnames = ['card_type', 'card_number', 'amount_total', 'status', 'employee', 'employee_code', 'company', 'device',
              'airplane', 'date_time', 'AID', 'AIP', 'RRN', 'TSI', 'CVMR', 'TVR', 'goods_services', 'seat', 'key_hash']


async def _clear_old_cookies(bot: Bot):
    """
    Удалит раз в сутки вчерашние файлы с куками.
    :return:
    """
    cookies_dir = os.path.join('joinpay', 'cookies')

    while True:
        if not os.path.exists(cookies_dir):
            return
        yesterday = datetime.utcnow() - timedelta(days=1)
        for cf in os.listdir(cookies_dir):
            if yesterday.strftime("%Y-%m-%d") not in cf:
                continue
            cookies_file_name = os.path.join(cookies_dir, cf)
            try:
                os.remove(cookies_file_name)
            except Exception as e:
                print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
        await asyncio.sleep(60 * 60 * 24)


async def _check_cookies(login: str) -> aiohttp.cookiejar.BaseCookie:
    now = datetime.utcnow()
    _cookies_name = f'{login}{now.strftime("%Y-%m-%d")}'
    _cookies_hash_object = hashlib.md5(_cookies_name.encode(encoding='UTF-8'))
    _cookies_file_name = os.path.join('joinpay', 'cookies',
                                      f'{now.strftime("%Y-%m-%d")}_{_cookies_hash_object.hexdigest()}.cookies')
    if not os.path.exists(_cookies_file_name):
        return aiohttp.cookiejar.BaseCookie()
    _cookies = aiohttp.cookiejar.BaseCookie()
    with open(_cookies_file_name, 'r') as _cookies_file:
        for _c in _cookies_file.readlines():
            _rawdata = _c.replace('Set-Cookie: ', '') + ';'
            _cookies.load(rawdata=_rawdata)
    return _cookies


async def auth(login: str, request_headers: dict, request_payload: aiohttp.FormData,
               server: str) -> aiohttp.cookiejar.BaseCookie:
    now = datetime.utcnow()
    _base_cookies = {}

    response_cookies = await _check_cookies(login=login)
    if response_cookies.get('csrftoken', '') != '':
        response_cookies.update(_base_cookies)
        return response_cookies

    request_cookies, csrfmiddlewaretoken = await get_csrfmiddlewaretoken(request_headers=request_headers,
                                                                         server=server)

    request_payload.add_field('csrfmiddlewaretoken', csrfmiddlewaretoken)
    # request_payload.add_field('DEBUG', True)
    # print(request_cookies.items())
    async with aiohttp.ClientSession(cookies=request_cookies) as session:
        try:
            # request_headers['content-length'] = '143'
            resp = await session.post(
                url=f'{server}/auth/login/',
                # cookies=request_cookies,
                headers=request_headers,
                data=request_payload,
                ssl=False,
            )
            body = await resp.text()
            # print(body)
        except Exception as e:
            print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
            return response_cookies
        response_cookies = session.cookie_jar.filter_cookies(URL(server))
        _cookies_name = f'{login}{now.strftime("%Y-%m-%d")}'
        _cookies_hash_object = hashlib.md5(_cookies_name.encode(encoding='UTF-8'))
        _joinpay_path = os.path.join('joinpay', 'cookies')
        try:
            os.makedirs(name=_joinpay_path, mode=0o775)
        except Exception as e:
            pass
        finally:
            _cookies_file_name = os.path.join(_joinpay_path,
                                              f'{now.strftime("%Y-%m-%d")}_{_cookies_hash_object.hexdigest()}.cookies')
        with open(_cookies_file_name, 'w') as _cookies_file:
            _cookies_file.write(response_cookies.output())

        response_cookies.update(_base_cookies)
        return response_cookies


async def get_csrfmiddlewaretoken(request_headers: dict, server: str) -> tuple:
    async with aiohttp.ClientSession(cookies=aiohttp.cookiejar.BaseCookie()) as session:
        try:
            resp = await session.get(
                url=f'{server}/auth/login/',
                headers=request_headers,
                ssl=False,
            )
            body = await resp.text()
        except Exception as e:
            print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
            return (dict(), '')
        soup = BeautifulSoup(body, 'lxml')
        token_input = soup.find('input', attrs={'name': 'csrfmiddlewaretoken'})
        if token_input is None:
            return (dict(), '')
        _cookies = aiohttp.cookiejar.BaseCookie()
        _cookies_data = session.cookie_jar.filter_cookies(URL(server)).output().split('\n')
        for _c in session.cookie_jar.filter_cookies(URL(server)).items():
            _rawdata = f'{_c[0]}={_c[1]};'
            _cookies.load(rawdata=_rawdata)
        return (
            _cookies,
            token_input.attrs.get('value', '')
        )


async def table_crawler(bot: Bot, login: str, password: str, server: str):
    # Заголовки запроса.
    request_headers = {
        'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
        'Cache-control': "no-cache",
        'Accept-encoding': "gzip, deflate, br",
        'Content-Type': "application/x-www-form-urlencoded",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        'Accept-language': "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        'Pragma': 'no-cache',
        'Referer': f'{server}/companies/',
        'Sec-Ch-Ua': '" Not A;Brand";v="99", "Chromium";v="90"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Origin': f'{server}',
    }

    #  Сылка нас траницу списка транзакций.
    transactions_page = f'{server}/air/transactions/'

    _joinpay_dir = os.path.join('joinpay')
    _cache_dir = os.path.join(_joinpay_dir, 'cache')
    if not os.path.exists(_cache_dir):
        try:
            os.makedirs(_cache_dir)
        except Exception as e:
            print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
    # Файл-хранилище обработанных транзакций.
    _cache_name = os.path.join(_cache_dir, 'transactions.cache')
    # Файл-хранилище транзакций со статусом, отличным от "оплачено".
    _bad_status = os.path.join(_cache_dir, 'transactions.bad')

    # Путь к общей папке, в которой храним файловую базу.
    _share_dir = os.path.join(_joinpay_dir, 'share')
    if not os.path.exists(_share_dir):
        try:
            os.makedirs(_share_dir)
        except Exception as e:
            print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')

    while True:

        # Авторизационные заголовки запроса.
        auth_headers = {
            'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
            'Cache-control': "no-cache",
            'Accept-encoding': "gzip, deflate, br",
            'Content-Type': "application/x-www-form-urlencoded",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            'Accept-language': "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            'Pragma': 'no-cache',
            'Referer': f'{server}/auth/login/?next=/',
            'Sec-Ch-Ua': '" Not A;Brand";v="99", "Chromium";v="90"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Origin': f'{server}',
        }
        # Данные формы авторизации.
        form_auth = aiohttp.FormData()
        form_auth.add_field('username', CFG['other']['login'])
        form_auth.add_field('password', CFG['other']['password'])
        # Авторизация (получение кук).
        auth_cookies = await auth(
            login=login,
            server=server,
            request_headers=auth_headers,
            request_payload=form_auth,
        )
        if auth_cookies.get('csrftoken', '') == '':
            await asyncio.sleep(60)
            continue

        now = datetime.utcnow()

        now.tzname()

        pages = [1]
        # pages = list(range(1, 34))
        last_page_n = 1

        async with aiohttp.ClientSession(cookies=auth_cookies) as session:
            for page in pages:
                _current_page_url = transactions_page + f'?page={page}'
                print(f'{datetime.utcnow().isoformat(sep="T")}: {_current_page_url}')
                try:
                    resp = await session.get(
                        url=_current_page_url,
                        headers=request_headers,
                        ssl=False
                    )
                except Exception as e:
                    print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                    await asyncio.sleep(60)
                    continue
                try:
                    body = await resp.text()
                except Exception as e:
                    print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                    await asyncio.sleep(15)
                    continue
                soup = BeautifulSoup(body, 'lxml')
                pagination = soup.find('ul', attrs={'class': 'pagination m-0'})
                if pagination is not None:
                    pages_titles = [e.text for e in pagination.children if e.name is not None]
                    if len(pages_titles) > 1:
                        last_page_n = int(pages_titles[-1])
                table = soup.find('table', attrs={'class': 'table table-hover m-0 text-center'})
                if table is None:
                    await asyncio.sleep(60)
                    continue

                _hash_transactions_from_cache = list()
                try:
                    with open(_cache_name, 'r') as cf:
                        _hash_transactions_from_cache = cf.readlines()
                except Exception as e:
                    print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                _hash_transactions_from_cache = [v.strip() for v in _hash_transactions_from_cache]

                transactions_list = list()
                for tr_transaction in table.find_all('tr', attrs={'class': 'link'}):
                    # Заготовка структуры транзакции.
                    transaction = {
                        'card_type': '—',
                        'card_number': '—',
                        'amount_total': 0,
                        'status': '—',
                        'employee': '—',
                        'employee_code': '—',
                        'company': '—',
                        'device': '—',
                        'airplane': '—',
                        'date_time': '—',
                        'AID': '—',
                        'AIP': '—',
                        'RRN': '—',
                        'TSI': '—',
                        'CVMR': '—',
                        'TVR': '—',
                        'goods_services': [],
                        'seat': '—',
                        'key_hash': '—',
                    }

                    transaction_fields = [e for e in tr_transaction.children if e.name is not None]
                    if len(transaction_fields) < 10:
                        continue
                    #     Тип оплаты ищем по атрибуту картинки.
                    _img_card = transaction_fields[0].find('img')
                    if _img_card is not None:
                        transaction['card_type'] = _img_card.attrs.get('data-original-title', '')

                    # Номер карты.
                    transaction['card_number'] = str(transaction_fields[1].text).strip()

                    # Сумма оплаты.
                    _amount_total = str(transaction_fields[2].text).strip()
                    _amount_total = re.findall(r'(\d{1,}\.\d{2})', _amount_total)
                    if len(_amount_total) != 0:
                        transaction['amount_total'] = float(_amount_total[0])
                    # Статус транзакции.
                    transaction['status'] = str(transaction_fields[3].text).strip()

                    # Данные сотрудника.
                    _employee = str(transaction_fields[4].text).strip()
                    transaction['employee'] = _employee

                    # Табельный номер сотрудника.
                    _employee_data = re.findall(r"\(([^)]*)\)", _employee)
                    if len(_employee_data) > 0:
                        transaction['employee_code'] = f"`{str(_employee_data[-1])}"

                    #     Компания.
                    transaction['company'] = str(transaction_fields[5].text).strip()
                    # Устройство.
                    transaction['device'] = str(transaction_fields[6].text).strip()
                    # ВС.
                    transaction['airplane'] = str(transaction_fields[7].text).strip()
                    # Дата и время транзакции.
                    transaction['date_time'] = str(transaction_fields[9].text).strip()

                    # Получение данных e-slip
                    _e_slip_url = ''
                    _e_slip_url_tag = transaction_fields[8].find('a', href=True)
                    if _e_slip_url_tag is not None:
                        _e_slip_url = _e_slip_url_tag.attrs.get('data-url', '')
                    if _e_slip_url != '':
                        _e_slip_url = f'{server}{_e_slip_url}'
                        _eslip_hdrs = request_headers.copy()
                        _eslip_hdrs['accept'] = '*/*'
                        _eslip_hdrs['referer'] = f'{server}/air/transactions/'
                        _eslip_hdrs['x-requested-wit'] = 'XMLHttpRequest'
                        _eslip_hdrs['Sec-Fetch-Dest'] = 'empty'
                        _eslip_hdrs['Sec-Fetch-Mode'] = 'cors'

                        try:
                            resp = await session.get(
                                url=_e_slip_url,
                                headers=_eslip_hdrs,
                                ssl=False
                            )
                        except Exception as e:
                            print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                            await asyncio.sleep(60)
                            continue
                        try:
                            _e_slip_body = await resp.text()
                        except Exception as e:
                            print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                            await asyncio.sleep(15)
                            continue
                        _e_slip_soup = BeautifulSoup(_e_slip_body, 'lxml')
                        _receipt_raw = str(_e_slip_soup.text).strip().split('\n')
                        _receipt_raw = [v.strip() for v in _receipt_raw if v.strip() != '']

                        _is_goods_list = False
                        for line in _receipt_raw:
                            if line.startswith('AID'):
                                _f = line.split(' ')
                                if len(_f) > 1:
                                    transaction['AID'] = _f[1]

                            if line.startswith('TSI'):
                                _f = line.split(' ')
                                if len(_f) > 1:
                                    transaction['TSI'] = _f[1]

                            if line.startswith('AIP'):
                                _f = line.split(' ')
                                if len(_f) > 1:
                                    transaction['AIP'] = _f[1]

                            if line.startswith('CVMR'):
                                _f = line.split(' ')
                                if len(_f) > 1:
                                    transaction['CVMR'] = _f[1]

                            if line.startswith('RRN'):
                                _f = line.split(' ')
                                if len(_f) > 1:
                                    transaction['RRN'] = _f[1]

                            if line.startswith('TVR'):
                                _f = line.split(' ')
                                if len(_f) > 1:
                                    transaction['TVR'] = _f[1]

                            if line.startswith('Список товаров'):
                                _is_goods_list = True
                                continue

                            if line.startswith('Место'):
                                transaction['seat'] = line.lower().replace('место', '').strip().upper()
                                _is_goods_list = False
                                continue

                            if line.startswith('Терминал'):
                                _is_goods_list = False
                                continue

                            if _is_goods_list:
                                line = line.replace('\xa0', '')
                                line = line.replace('₽', '')

                                _good_title = '—'
                                _good_title_data = re.findall(r'"[^"]*"', line)
                                if len(_good_title_data) > 0:
                                    _good_title = str(_good_title_data[-1]).strip().replace('"', '')

                                _good_amount_str = line.replace(_good_title, '')
                                _good_amount_str = _good_amount_str.replace('"', '')
                                _good_amount = 0
                                _good_amount_v = re.findall(r'(\d{1,}\.\d{2})', _good_amount_str)
                                if len(_good_amount_v) != 0:
                                    _good_amount = float(str(_good_amount_v[-1]))

                                _factor = 1
                                _factor_data = _good_amount_str.split('×')
                                if len(_factor_data) > 1:
                                    _factor = int(str(_factor_data[0]).strip())
                                # НДС попробуем вытаскивать из названия товара/услуги.
                                _vat_data = re.findall(r'НДС.*?(\d+)', _good_title)
                                _vat = 0.0
                                if len(_vat_data) > 0:
                                    _vat = float(str(_vat_data[-1]).strip())

                                _vat_amount = (_good_amount * _vat) / (100 + _vat)
                                _vat_amount = round(_vat_amount, 2)
                                # Собреём товары и услуги в отдельный список - поле транзакции.
                                for f in range(0, _factor):
                                    transaction['goods_services'].append({
                                        'title': _good_title,
                                        'amount': _good_amount,
                                        'vat': _vat,
                                        'vat_amount': _vat_amount,
                                    })

                            # Соберём список товаров/услуг в дам JSON, для того,
                            # чтоб сложить выбранные поля в строку и получить уникальный идентификатор транзакции.
                            _goods_services_str = json.dumps(transaction.get('goods_services'))
                            key_cache_str = f"{transaction.get('card_number')}{transaction.get('amount_total')}{_goods_services_str}{transaction.get('date_time')}"
                            key_cache_obj = hashlib.md5(key_cache_str.encode(encoding='UTF-8'))
                            transaction['key_hash'] = key_cache_obj.hexdigest()

                    # Закэшируем тр-ии с плохим статусом.
                    try:
                        with open(_bad_status, 'a') as bs:
                            if str(transaction.get('status')).strip().lower() != 'оплачено':
                                key_cache = transaction.get('key_hash')
                                bs.write(key_cache + '\n')
                    except Exception as e:
                        print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')

                    # Вычислим хеш транзакции, проверим, нет ли такой в кэше.
                    key_cache = transaction.get('key_hash')
                    if key_cache in _hash_transactions_from_cache:
                        # Пропустим уже обработанные транзакции.
                        continue
                    print(
                        f"{datetime.utcnow().isoformat(sep='T')}:{transaction.get('card_number')}-{transaction.get('amount_total')}")
                    transactions_list.append(transaction)

                    await asyncio.sleep(1)

                # Закешируем транзакции, чтоб дважды не попадались одни и те же.
                try:
                    with open(_cache_name, 'a') as cf:
                        for tr in transactions_list:
                            key_cache = tr.get('key_hash')
                            cf.write(key_cache + '\n')
                except Exception as e:
                    print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')

                if len(transactions_list) != 0:
                    # Группировка транзакций по месяцам.
                    transactions_list_by_month = {}
                    # Группировка транзакция по дням.
                    transactions_list_day = {}

                    # Собрать тр-ии по дню и месяцу.
                    for tr in transactions_list:
                        tr_date_str = tr.get('date_time')  # 03.05.21 03:59:08
                        try:
                            tr_date = datetime.strptime(tr_date_str, '%d.%m.%y %H:%M:%S')
                        except Exception as e:
                            print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                            continue
                        _key_month = tr_date.strftime('%Y-%m')
                        _list_month = transactions_list_by_month.get(_key_month, [])
                        _list_month.append(tr)
                        transactions_list_by_month[_key_month] = _list_month

                        _key_day = tr_date.strftime('%Y-%m-%d')
                        _list_day = transactions_list_day.get(_key_day, [])
                        _list_day.append(tr)
                        transactions_list_day[_key_day] = _list_day

                    # Записать тр-ии по месяцу.
                    if len(transactions_list_by_month) != 0:
                        for _key in transactions_list_by_month.keys():
                            # Тут пока оставлю код в таком виде, если захотим раскидывать по месяцам.
                            # csv_path = os.path.join(_joinpay_dir, f'join_pay_{_key}.csv')
                            csv_path = os.path.join(_share_dir, 'join_pay_full.csv')
                            _transactions_month = transactions_list_by_month.get(_key)
                            with open(csv_path, 'a', newline='') as csvfile:
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                for t in _transactions_month:
                                    _goods_services = ''
                                    for gs in t.get('goods_services'):
                                        _goods_services += f'{gs.get("title")}|\t{gs.get("amount")}|\tСтавка НДС: {gs.get("vat")}%|\tСумма НДС: {gs.get("vat_amount")}\n'
                                    t['goods_services'] = _goods_services.rstrip('\n')
                                    writer.writerow(t)

                    # Записать тр-ии по дню.
                    if len(transactions_list_day) != 0:
                        for _key in transactions_list_day.keys():
                            csv_path = os.path.join(_joinpay_dir, f'join_pay_{_key}.csv')
                            _transactions_day = transactions_list_day.get(_key)

                            with open(csv_path, 'a', newline='') as csvfile:
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                for t in _transactions_day:
                                    writer.writerow(t)

                # Спим n секунд между страницами
                await asyncio.sleep(2)

        if last_page_n != 1:
            # Будем искать отложенные транзакции.
            pages = list(range(1, last_page_n + 1))
            bad_tr_hashes = list()
            try:
                with open(_bad_status, 'r') as bs:
                    bad_tr_hashes = [l.strip() for l in bs.readlines()]
                    bad_tr_hashes = list(set(bad_tr_hashes))
            except Exception as e:
                print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
            _tmp_bad_tr_hashes = bad_tr_hashes.copy()
            data_base = list()
            csv_path = os.path.join(_share_dir, 'join_pay_full.csv')
            with open(csv_path, 'r', newline='') as csvfile:
                # Читальщик CSV в - читает каждую строку в словарь с ключами из заголовков.
                reader = csv.DictReader(csvfile, fieldnames=fieldnames)
                for row in reader:
                    data_base.append(row)

            if len(bad_tr_hashes) != 0:
                async with aiohttp.ClientSession(cookies=auth_cookies) as session:
                    for page in pages:
                        _current_page_url = transactions_page + f'?page={page}'
                        print(f'{datetime.utcnow().isoformat(sep="T")}: проверка статусов {_current_page_url}')
                        try:
                            resp = await session.get(
                                url=_current_page_url,
                                headers=request_headers,
                                ssl=False
                            )
                        except Exception as e:
                            print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                            await asyncio.sleep(60)
                            continue
                        try:
                            body = await resp.text()
                        except Exception as e:
                            print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                            await asyncio.sleep(15)
                            continue
                        soup = BeautifulSoup(body, 'lxml')
                        table = soup.find('table', attrs={'class': 'table table-hover m-0 text-center'})
                        if table is None:
                            await asyncio.sleep(60)
                            continue

                        _hash_transactions_from_cache = list()
                        try:
                            with open(_cache_name, 'r') as cf:
                                # _hash_transactions_from_cache.append(cf.readline())
                                _hash_transactions_from_cache = cf.readlines()
                        except Exception as e:
                            print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                        _hash_transactions_from_cache = [v.strip() for v in _hash_transactions_from_cache]

                        transactions_list = list()
                        for tr_transaction in table.find_all('tr', attrs={'class': 'link'}):
                            transaction = {
                                'card_type': '—',
                                'card_number': '—',
                                'amount_total': 0,
                                'status': '—',
                                'employee': '—',
                                'employee_code': '—',
                                'company': '—',
                                'device': '—',
                                'airplane': '—',
                                'date_time': '—',
                                'AID': '—',
                                'AIP': '—',
                                'RRN': '—',
                                'TSI': '—',
                                'CVMR': '—',
                                'TVR': '—',
                                'goods_services': [],
                                'seat': '—',
                                'key_hash': '—',
                            }

                            transaction_fields = [e for e in tr_transaction.children if e.name is not None]
                            if len(transaction_fields) < 10:
                                continue
                            _img_card = transaction_fields[0].find('img')
                            if _img_card is not None:
                                transaction['card_type'] = _img_card.attrs.get('data-original-title', '')

                            transaction['card_number'] = str(transaction_fields[1].text).strip()
                            _amount_total = str(transaction_fields[2].text).strip()
                            _amount_total = re.findall(r'(\d{1,}\.\d{2})', _amount_total)
                            if len(_amount_total) != 0:
                                transaction['amount_total'] = float(_amount_total[0])

                            transaction['status'] = str(transaction_fields[3].text).strip()
                            _employee = str(transaction_fields[4].text).strip()
                            transaction['employee'] = _employee
                            _employee_data = re.findall(r"\(([^)]*)\)", _employee)
                            if len(_employee_data) > 0:
                                transaction['employee_code'] = f"`{str(_employee_data[-1])}"
                            transaction['company'] = str(transaction_fields[5].text).strip()
                            transaction['device'] = str(transaction_fields[6].text).strip()
                            transaction['airplane'] = str(transaction_fields[7].text).strip()
                            transaction['date_time'] = str(transaction_fields[9].text).strip()

                            _e_slip_url = ''
                            _e_slip_url_tag = transaction_fields[8].find('a', href=True)
                            if _e_slip_url_tag is not None:
                                _e_slip_url = _e_slip_url_tag.attrs.get('data-url', '')
                            if _e_slip_url != '':
                                _e_slip_url = f'{server}{_e_slip_url}'
                                _eslip_hdrs = request_headers.copy()
                                _eslip_hdrs['accept'] = '*/*'
                                _eslip_hdrs['referer'] = f'{server}/air/transactions/'
                                _eslip_hdrs['x-requested-wit'] = 'XMLHttpRequest'
                                _eslip_hdrs['Sec-Fetch-Dest'] = 'empty'
                                _eslip_hdrs['Sec-Fetch-Mode'] = 'cors'

                                try:
                                    resp = await session.get(
                                        url=_e_slip_url,
                                        headers=_eslip_hdrs,
                                        ssl=False
                                    )
                                except Exception as e:
                                    print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                                    await asyncio.sleep(60)
                                    continue
                                try:
                                    _e_slip_body = await resp.text()
                                except Exception as e:
                                    print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
                                    await asyncio.sleep(15)
                                    continue
                                _e_slip_soup = BeautifulSoup(_e_slip_body, 'lxml')
                                _receipt_raw = str(_e_slip_soup.text).strip().split('\n')
                                _receipt_raw = [v.strip() for v in _receipt_raw if v.strip() != '']

                                _is_goods_list = False
                                for line in _receipt_raw:
                                    if line.startswith('AID'):
                                        _f = line.split(' ')
                                        if len(_f) > 1:
                                            transaction['AID'] = _f[1]

                                    if line.startswith('TSI'):
                                        _f = line.split(' ')
                                        if len(_f) > 1:
                                            transaction['TSI'] = _f[1]

                                    if line.startswith('AIP'):
                                        _f = line.split(' ')
                                        if len(_f) > 1:
                                            transaction['AIP'] = _f[1]

                                    if line.startswith('CVMR'):
                                        _f = line.split(' ')
                                        if len(_f) > 1:
                                            transaction['CVMR'] = _f[1]

                                    if line.startswith('RRN'):
                                        _f = line.split(' ')
                                        if len(_f) > 1:
                                            transaction['RRN'] = _f[1]

                                    if line.startswith('TVR'):
                                        _f = line.split(' ')
                                        if len(_f) > 1:
                                            transaction['TVR'] = _f[1]

                                    if line.startswith('Список товаров'):
                                        _is_goods_list = True
                                        continue

                                    if line.startswith('Место'):
                                        transaction['seat'] = line.lower().replace('место', '').strip().upper()
                                        _is_goods_list = False
                                        continue

                                    if line.startswith('Терминал'):
                                        _is_goods_list = False
                                        continue

                                    if _is_goods_list:
                                        line = line.replace('\xa0', '')
                                        line = line.replace('₽', '')

                                        _good_title = '—'
                                        _good_title_data = re.findall(r'"[^"]*"', line)
                                        if len(_good_title_data) > 0:
                                            _good_title = str(_good_title_data[-1]).strip().replace('"', '')

                                        _good_amount_str = line.replace(_good_title, '')
                                        _good_amount_str = _good_amount_str.replace('"', '')
                                        _good_amount = 0
                                        _good_amount_v = re.findall(r'(\d{1,}\.\d{2})', _good_amount_str)
                                        if len(_good_amount_v) != 0:
                                            _good_amount = float(str(_good_amount_v[-1]))

                                        _factor = 1
                                        _factor_data = _good_amount_str.split('×')
                                        if len(_factor_data) > 1:
                                            _factor = int(str(_factor_data[0]).strip())
                                        _vat_data = re.findall(r'НДС.*?(\d+)', _good_title)
                                        _vat = 0.0
                                        if len(_vat_data) > 0:
                                            _vat = float(str(_vat_data[-1]).strip())

                                        _vat_amount = (_good_amount * _vat) / (100 + _vat)
                                        _vat_amount = round(_vat_amount, 2)

                                        for f in range(0, _factor):
                                            transaction['goods_services'].append({
                                                'title': _good_title,
                                                'amount': _good_amount,
                                                'vat': _vat,
                                                'vat_amount': _vat_amount,
                                            })

                                    _goods_services_str = json.dumps(transaction.get('goods_services'))
                                    key_cache_str = f"{transaction.get('card_number')}{transaction.get('amount_total')}{_goods_services_str}{transaction.get('date_time')}"
                                    key_cache_obj = hashlib.md5(key_cache_str.encode(encoding='UTF-8'))
                                    transaction['key_hash'] = key_cache_obj.hexdigest()

                            # Вычислим хеш транзакции, проверим, нет ли такой в кэше плохих статусов.
                            key_cache = transaction.get('key_hash')
                            if key_cache not in bad_tr_hashes:
                                continue

                            try:
                                _tmp_bad_tr_hashes.remove(key_cache)
                            except ValueError as ve:
                                print(
                                    f'{datetime.utcnow().isoformat(sep="T")}: _tmp_bad_tr_hashes.remove({key_cache}) {ve}')
                            print(
                                f"{datetime.utcnow().isoformat(sep='T')}: проверяем статус транзакции: {transaction.get('card_number')}-{transaction.get('amount_total')} - {transaction.get('status')}")
                            if str(transaction.get('status')).strip().lower() == 'оплачено':
                                print(
                                    f"{datetime.utcnow().isoformat(sep='T')}: {transaction.get('card_number')}-{transaction.get('amount_total')} - добавлена на обновление")
                                transactions_list.append(transaction)

                            await asyncio.sleep(1)

                        if len(transactions_list) != 0:
                            # Обновить статус транзакций.

                            csv_path = os.path.join(_share_dir, 'join_pay_full_upd.csv')
                            with open(csv_path, 'a', newline='') as csvfile:
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                for tr in transactions_list:
                                    for db in data_base:
                                        if tr.get('key_hash') == db.get('key_hash'):
                                            db['status'] = tr.get('status')
                                            writer.writerow(tr)
                                            try:
                                                bad_tr_hashes.remove(tr.get('key_hash'))
                                            except ValueError as ve:
                                                print(
                                                    f'{datetime.utcnow().isoformat(sep="T")}: bad_tr_hashes.remove({tr.get("key_hash")}) {ve}')
                                            print(
                                                f"{datetime.utcnow().isoformat(sep='T')}: {tr.get('card_number')}-{tr.get('amount_total')} - обновлена")

                        if len(_tmp_bad_tr_hashes) == 0:
                            break

                        # Спим n секунд между страницами
                        await asyncio.sleep(2)

            # Закэшируем тр-ии с плохим статусом.
            try:
                with open(_bad_status, 'w') as bs:
                    for bth in bad_tr_hashes:
                        bs.write(bth + '\n')
            except Exception as e:
                print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')

            csv_path = os.path.join(_share_dir, 'join_pay_full.csv')
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for t in data_base:
                    writer.writerow(t)

        # Спим n секунд.
        await asyncio.sleep(3600)


async def start_handler(event: types.Message):
    print(f'{datetime.utcnow().isoformat(sep="T")}: {event}')


async def _start_polling(disp: Dispatcher) -> bool:
    try:
        await disp.start_polling()
    except Exception as e:
        print(f'{datetime.utcnow().isoformat(sep="T")}: {e}')
        return True


# Телеграм бот, чтоб рассылать что-то в телеграм.
async def bot_worker(bot: Bot):
    dis = Dispatcher(bot=bot)
    _error = await _start_polling(disp=dis)
    while _error:
        await asyncio.sleep(60)
        _error = await _start_polling(disp=dis)


async def main():
    global CFG
    try:
        with open(CFG_PATH, 'r') as yml_file:
            CFG = yaml.load(yml_file, Loader=yaml.FullLoader)
    except FileNotFoundError:
        print(f'Укажите файл конфигурации {CFG_PATH}')
    else:
        bot = Bot(token=CFG['other']['bot'])
        await asyncio.gather(
            # bot_worker(bot),
            table_crawler(
                bot=bot,
                login=CFG['other']['login'],
                password=CFG['other']['password'],
                server=CFG['other']['server'],
            ),
            _clear_old_cookies(bot),
        )
        # try:
        #     await asyncio.gather(
        #         bot_worker(bot),
        #         table_crawler(
        #             bot=bot,
        #             login=CFG['other']['login'],
        #             password=CFG['other']['password'],
        #             server=CFG['other']['server'],
        #         ),
        #         _clear_old_cookies(bot),
        #     )
        # except TelegramAPIError as tgError:
        #     print(f'{datetime.utcnow().isoformat(sep="T")}: {tgError}')
        # except ClientConnectorError as clError:
        #     print(f'{datetime.utcnow().isoformat(sep="T")}: {clError}')
        # except Exception as err:
        #     print(f'{datetime.utcnow().isoformat(sep="T")}: {err}')


# Конвертер дат для сериализации/десериализации JSON.
def my_converter(o):
    if isinstance(o, datetime):
        return o.__str__()


try:
    asyncio.run(main())
except KeyboardInterrupt:
    sys.exit(0)
