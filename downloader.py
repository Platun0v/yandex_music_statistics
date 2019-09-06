import argparse
import requests
import logging
import sys
import config
import re

logger = logging.getLogger('Yandex')
formatter = logging.Formatter(
    '%(asctime)s (%(filename)s:%(lineno)d) %(levelname)s - %(name)s: "%(message)s"'
)

console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)

logger.setLevel(logging.DEBUG)


class Yandex:
    main_url = f'https://yandex.ru'

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.session = requests.Session()
        self.update_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
        })

    def auth(self):
        self.update_main_url('passport.yandex.ru')

        auth_page = self.get('/auth').text
        csrf_token, process_uuid = self.find_auth_data(auth_page)

        track_id = self.post('/registration-validations/auth/multi_step/start',
                             data={'csrf_token': csrf_token,
                                   'process_uuid': process_uuid,
                                   'login': self.login}).json()['track_id']

        result = self.post('/registration-validations/auth/multi_step/commit_password',
                           data={'csrf_token': csrf_token,
                                 'track_id': track_id,
                                 'password': self.password}).json()

        user_data = self.post('/registration-validations/auth/accounts',
                              data={'csrf_token': csrf_token}).json()

        return user_data

    def get(self, url, params=None, **kwargs):
        return self.method('GET', f'{self.main_url}/{url if url[0] != "/" else url[1:]}', params=params, **kwargs)

    def post(self, url, data=None, **kwargs):
        return self.method('POST', f'{self.main_url}/{url if url[0] != "/" else url[1:]}', data=data, **kwargs)

    def method(self, method, url, **kwargs):
        if method == 'POST':
            logger.info(f'POST to {url} with {kwargs}')
            resp = self.session.post(url, **kwargs)
        elif method == 'GET':
            logger.info(f'GET to {url} with {kwargs}')
            resp = self.session.get(url, **kwargs)
        else:
            raise ValueError(f'Unknown method {method}', method)
        logger.debug(f'Got {resp.text}')
        return resp

    def update_headers(self, headers):
        self.session.headers.update(headers)

    def update_main_url(self, url):
        self.main_url = f'https://{url}'

    @staticmethod
    def find_auth_data(html):
        csrf_token = re.search('data-csrf="\S*"', html)
        csrf_token = html[csrf_token.start():csrf_token.end()][11:-1]
        process_uuid = re.search('process_uuid=\S*"', html)
        process_uuid = html[process_uuid.start():process_uuid.end()][13:-1]

        return csrf_token, process_uuid


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--login', help='Your yandex login', type=str, required=True)
    # parser.add_argument('--password', help='Your yandex password', type=str, required=True)
    # args = parser.parse_args()

    # Yandex(args.login, args.password)
    yandex = Yandex(config.login, config.password)

    print(yandex.auth())
