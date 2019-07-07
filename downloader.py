from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from dataclasses import dataclass
import pickle
import config


@dataclass
class Track:
    data_b: int
    track_name: str
    track_artist: str
    url_track: str
    url_artist: str


def find_element(browser_, by, value, timeout=1, attempts=3):
    for _ in range(attempts):
        try:
            elem = browser_.find_element(by, value)
            return elem
        except Exception as e:
            sleep(timeout)

    return browser_.find_element(by, value)


def find_elements(browser_, by, value, timeout=1, attempts=3):
    for _ in range(attempts):
        try:
            elem = browser_.find_elements(by, value)
            return elem
        except Exception as e:
            print(e)
            sleep(timeout)

    return browser_.find_elements(by, value)


def get_attribute(browser_, value, timeout=1, attempts=3):
    for _ in range(attempts):
        elem = browser_.get_attribute(value)
        if elem:
            return elem
        else:
            scroll_down()
            sleep(timeout)

    return browser_.get_attribute(value)


def scroll_down(times=3):
    html_ = find_element(browser, By.TAG_NAME, 'html')
    for _ in range(times):
        html_.send_keys(Keys.PAGE_DOWN)


login = config.login
password = config.password
browser = webdriver.Chrome('chromedriver.exe')
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

sleep(5)  # Wait for redirect to passp.yandex.ru

browser.get(f'https://music.yandex.ru/users/{login}/history')

res = []
data_b_in_res = []

flag = True

while flag:
    tracks = find_elements(browser, By.CLASS_NAME, 'd-track')

    def process_tracks(tracks_, flg=False):
        for track in tracks_:
            data_b = int(get_attribute(track, 'data-b'))

            if data_b not in data_b_in_res:
                flg = True

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

        return flg
    try:
        flag = process_tracks(tracks, flag)
    except Exception:
        print(len(res))
    scroll_down(10)

    with open('res.pkl', 'wb') as f:
        pickle.dump(res, f)

res.sort(key=lambda x: x.data_b)
print(*res, sep='\n')
