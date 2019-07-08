from time import sleep
from dataclasses import dataclass
import pickle
import argparse

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common import exceptions


@dataclass
class Track:
    data_b: int
    track_name: str
    track_artist: str
    url_track: str
    url_artist: str


def find_element(self, by=By.ID, value=None, timeout=1, attempts=3):
    for _ in range(attempts):
        try:
            elem = self.find_element(by, value)
            return elem
        except exceptions.NoSuchElementException:
            sleep(timeout)

    return self.find_element(by, value)


def find_elements(self, by=By.ID, value=None, timeout=1, attempts=3):
    for _ in range(attempts):
        try:
            elem = self.find_elements(by, value)
            return elem
        except exceptions.NoSuchElementException:
            sleep(timeout)

    return self.find_elements(by, value)


def get_attribute(sel_elem, value, timeout=1, attempts=3):
    for _ in range(attempts):
        elem = sel_elem.get_attribute(value)
        if elem:
            return elem
        else:
            scroll_down()
            sleep(timeout)

    return sel_elem.get_attribute(value)


def scroll_down(times=3):
    html_ = find_element(browser, By.TAG_NAME, 'html')
    for _ in range(times):
        html_.send_keys(Keys.PAGE_DOWN)


def main(login, password):
    browser = webdriver.Chrome('chromedriver.exe')
    global browser
    browser.get('https://passport.yandex.ru/auth')

    login_field = find_element(browser, By.ID, 'passp-field-login')
    login_field.send_keys(login)

    button = find_element(browser, By.CLASS_NAME, 'passp-sign-in-button')
    button = find_element(button, By.CLASS_NAME, 'passp-form-button')
    button.click()

    password_field = find_element(browser, By.ID, 'passp-field-passwd')
    password_field.send_keys(password)

    button = find_element(browser, By.CLASS_NAME, 'passp-sign-in-button')
    button = find_element(button, By.CLASS_NAME, 'passp-form-button')
    button.click()

    sleep(10)  # Wait for redirect to passp.yandex.ru

    nickname = find_element(browser, By.CLASS_NAME, 'personal-info-login__displaylogin').text
    browser.get(f'https://music.yandex.ru/users/{nickname}/history')

    res = []
    data_b_in_res = []

    flag = True

    while flag:
        tracks = find_elements(browser, By.CLASS_NAME, 'd-track')
        flag = False

        try:
            for track in tracks:
                data_b = int(get_attribute(track, 'data-b'))

                if data_b not in data_b_in_res:
                    flag = True

                    data_b_in_res.append(data_b)

                    name = find_element(track, By.CLASS_NAME, 'd-track__name')
                    track_name = get_attribute(name, 'title')
                    url_track = get_attribute(find_element(name, By.TAG_NAME, 'a'), 'href')

                    artist = find_element(find_element(track, By.CLASS_NAME, 'd-track__artists'), By.TAG_NAME, 'a')
                    track_artist = get_attribute(artist, 'title')
                    url_artist = get_attribute(artist, 'href')

                    res.append(Track(data_b=data_b,
                                     track_name=track_name,
                                     track_artist=track_artist,
                                     url_track=url_track,
                                     url_artist=url_artist))
        except Exception:
            pass
        scroll_down(10)

    with open('res.pkl', 'wb') as f:
        pickle.dump(res, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--login', help='Your yandex login', type=str, required=True)
    parser.add_argument('--password', help='Your yandex password', type=str, required=True)
    args = parser.parse_args()

    main(args.login, args.password)
