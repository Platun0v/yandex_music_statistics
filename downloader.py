import argparse
from time import sleep
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

logger.setLevel(logging.WARN)


class AuthError(Exception):
    pass


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

        self.tracks_library = {}

        self.sign = None
        self.experiments = None

    def auth(self):
        self.update_main_url('passport.yandex.ru')

        auth_page = self.get('/auth').text
        csrf_token, process_uuid = self.find_auth_data(auth_page)

        auth_login = self.post('/registration-validations/auth/multi_step/start',
                               data={'csrf_token': csrf_token,
                                     'process_uuid': process_uuid,
                                     'login': self.login}).json()
        if auth_login['status'] == 'error':
            raise AuthError(f'Got error {auth_login["errors"]}')

        auth_password = self.post('/registration-validations/auth/multi_step/commit_password',
                                  data={'csrf_token': csrf_token,
                                        'track_id': auth_login['track_data'],
                                        'password': self.password}).json()

        if auth_password['status'] == 'error':
            raise AuthError(f'Got error {auth_password["errors"]}')

        user_data = self.post('/registration-validations/auth/accounts',
                              data={'csrf_token': csrf_token}).json()

        return user_data

    def get_track_ids(self):
        self.update_main_url('music.yandex.ru')

        res = self.get('/handlers/library.jsx',
                       {'owner': self.login, 'filter': 'history', 'likeFilter': 'favorite', 'lang': 'ru',
                        'external-domain': 'music.yandex.ru', 'overembed': 'false', 'ncrnd': '0.9546193023464256'})
        tracks = res.json()
        track_ids = list(map(str, tracks['trackIds']))
        tracks = tracks['tracks']
        self.update_library(tracks, track_ids[:len(tracks)])

        return track_ids

    def update_library(self, tracks, track_ids_old):
        for track, track_id_old in zip(tracks, track_ids_old):
            track_id = str(track['id'])
            if self.tracks_library.get(track_id_old) is None and track['type'] == 'music':
                album = track['albums'][0] if len(track['albums']) > 0 else None
                duration_sec = track.get('durationMs') // 1000 if track.get('durationMs') else None

                self.tracks_library[track_id_old] = {
                    'artist': track['artists'][0]['name'], 'artist_id': track['artists'][0]['id'],
                    'album': album['title'] if album else None, 'album_id': album['id'] if album else None,
                    'track': track['title'], 'track_id': track_id,
                    'duration_sec': duration_sec, 'year': album.get('year') if album else None,
                    'genre': album.get('genre') if album else None,
                }

    def get_tracks_data(self, track_ids):
        if self.sign is None:
            self.sign, self.experiments = self.find_history_data(self.get(f'users/{self.login}/history').text)
        tracks_sm = 250

        track_ids = list(set(track_ids))
        track_ids = [track_ids[tracks_sm * i:tracks_sm * (i + 1)] for i in range(len(track_ids) // tracks_sm + 1)]

        for track_ids_sm in track_ids:
            resp = self.post('/handlers/track-entries.jsx', data={
                'entries': ','.join(track_ids_sm),
                'strict': 'true',
                'lang': 'ru',
                'sign': self.sign,
                'experiments': self.experiments,
                'external-domain': 'music.yandex.ru',
            }).json()
            self.update_library(resp, track_ids_sm)

            sleep(3)

    def download_and_safe_tracks(self):
        track_ids = self.get_track_ids()
        self.get_tracks_data(track_ids)
        self.save_csv(track_ids)

    def save_csv(self, track_ids):
        with open('statistics.csv', 'wb') as f:
            f_line = True

            for track_id in track_ids:
                track_data = []
                if self.tracks_library.get(track_id) is None:
                    continue

                if f_line:
                    f.write((','.join(self.tracks_library[track_id].keys()) + '\n').encode())
                    f_line = False

                for key in self.tracks_library[track_id]:
                    track_data.append(f'"{self.tracks_library[track_id][key]}"')
                f.write((','.join(track_data) + '\n').encode())

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
        csrf_token = re.search('data-csrf=".*?"', html)
        csrf_token = html[csrf_token.start():csrf_token.end()][11:-1]
        process_uuid = re.search('process_uuid=.*?"', html)
        process_uuid = html[process_uuid.start():process_uuid.end()][13:-1]

        return csrf_token, process_uuid

    @staticmethod
    def find_history_data(html):
        sign = re.search('"sign":".*?"', html)
        sign = html[sign.start():sign.end()][9:-1]
        experiments = re.search('"experiments":".*?"}', html)
        experiments = html[experiments.start():experiments.end()][16:-1]

        return sign, experiments


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--login', help='Your yandex login', type=str, required=True)
    parser.add_argument('--password', help='Your yandex password', type=str, required=True)
    args = parser.parse_args()

    yandex = Yandex(args.login, args.password)
    # yandex = Yandex(config.login, config.password)
    yandex.auth()
    yandex.download_and_safe_tracks()
