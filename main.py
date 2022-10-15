import logging
from urllib.parse import urlparse

import requests


# https://xkcd.com/353/
# https://xkcd.com/614/info.0.json

def get_img_name_from_path(url):
    logging.debug(url)

    index = url.rfind('/') + 1
    logging.debug(f"Index of beginning Python: {index} in {url}")
    return url[index:]


def fetch_xkcd_comix_url(comix_number):
    url = f"https://xkcd.com/{comix_number}/info.0.json"
    response = requests.get(url=url)
    response.raise_for_status()
    return response.json().get('img')


def save_xkcd_comix(comix_url):
    response = requests.get(comix_url)
    response.raise_for_status()
    comix = response.content

    comix_name = get_img_name_from_path(urlparse(comix_url).path)
    logging.info(f'Comix name: {comix_name}')
    with open(comix_name, 'wb') as file:
        file.write(comix)


def load_xkcd_comix(comix_number):
    try:
        comix_url = fetch_xkcd_comix_url(comix_number)
        save_xkcd_comix(comix_url)
    except requests.exceptions.HTTPError:
        logging.warning("Couldn't fetch or save url of xkcd image")


def main():
    logging.basicConfig(level=logging.DEBUG)
    load_xkcd_comix(353)


if __name__ == "__main__":
    main()