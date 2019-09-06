import argparse
import requests
import logging
import sys
import config


logger = logging.getLogger('Yandex')
formatter = logging.Formatter(
    '%(asctime)s (%(filename)s:%(lineno)d) %(levelname)s - %(name)s: "%(message)s"'
)

console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)

logger.setLevel(logging.INFO)


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
        pass

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


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--login', help='Your yandex login', type=str, required=True)
    # parser.add_argument('--password', help='Your yandex password', type=str, required=True)
    # args = parser.parse_args()

    # Yandex(args.login, args.password)
    Yandex(config.login, config.password)

    Yandex.auth()
