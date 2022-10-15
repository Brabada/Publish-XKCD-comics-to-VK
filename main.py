import logging
from urllib.parse import urlparse
import os
from pprint import pprint

from dotenv import load_dotenv
import requests


# https://xkcd.com/353/
# https://xkcd.com/614/info.0.json

def get_img_name_from_path(url):
    logging.debug(url)
    index = url.rfind('/') + 1
    logging.debug(f"Index of beginning Python: {index} in {url}")
    return url[index:]


def fetch_xkcd_comix_json(comix_number):
    url = f"https://xkcd.com/{comix_number}/info.0.json"
    response = requests.get(url=url)
    response.raise_for_status()
    return response.json()


def print_xkcd_alt_from_json(comix_json):
    print(comix_json.get('alt'))


def get_comix_url_from_json(json):
    return json.get('img')


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
        comix_json = fetch_xkcd_comix_json(comix_number)
        print_xkcd_alt_from_json(comix_json)
        comix_url = get_comix_url_from_json(comix_json)
        save_xkcd_comix(comix_url)
    except requests.exceptions.HTTPError:
        logging.warning("Couldn't fetch or save url of xkcd image")


def fetch_user_groups_from_vk(user_id):
    """Get users groups from VK by user_id_token"""
    method = 'groups.get'
    url = f'https://api.vk.com/method/{method}'
    params = {
        'access_token': user_id,
        'v': '5.131',
        'extended': '1',
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    response = response.json()
    pprint(response, sort_dicts=False)


def main():
    logging.basicConfig(level=logging.DEBUG)

    load_dotenv()
    client_id = os.getenv("VK_APP_CLIENT_ID")
    user_id = os.getenv('VK_USER_TOKEN')

    fetch_user_groups_from_vk(user_id)
    # load_xkcd_comix(353)


if __name__ == "__main__":
    main()