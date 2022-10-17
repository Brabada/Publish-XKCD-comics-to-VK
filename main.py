import random
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
    logging.debug(f"Index of beginning name: {index} in {url}")
    return url[index:]


def fetch_xkcd_comix_json(comix_number):
    url = f"https://xkcd.com/{comix_number}/info.0.json"
    response = requests.get(url=url)
    response.raise_for_status()
    return response.json()


def print_xkcd_alt_from_json(comix_json):
    return comix_json.get('alt')


def get_comix_url_from_json(json):
    return json.get('img')


def save_xkcd_comix(comix_url):
    response = requests.get(comix_url)
    response.raise_for_status()
    comix = response.content

    comix_file_name = get_img_name_from_path(urlparse(comix_url).path)
    logging.info(f'Comix name: {comix_file_name}')
    with open(comix_file_name, 'wb') as file:
        file.write(comix)
    return comix_file_name


def load_xkcd_comix(comix_number):
    try:
        comix_json = fetch_xkcd_comix_json(comix_number)
        alt = print_xkcd_alt_from_json(comix_json)
        comix_url = get_comix_url_from_json(comix_json)
        comix_file_name = save_xkcd_comix(comix_url)
    except requests.exceptions.HTTPError:
        logging.warning("Couldn't fetch or save url of xkcd image")
    return comix_file_name, alt

def get_random_xkcd_comix_num():
    response = requests.get('https://xkcd.com/info.0.json')
    response.raise_for_status()
    _to = response.json()['num']
    _from = 1
    return random.randint(_from, _to)


def load_random_xkcd_img():
    """Loads random XKCD comix from site and returns comix file name and alt"""

    comix_number = get_random_xkcd_comix_num()
    return load_xkcd_comix(comix_number)


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


def fetch_url_for_upload_img(user_id, group_id):
    """
    Takes group_id and return server address to upload image on group wall
    """

    method = 'photos.getWallUploadServer'
    url = f'https://api.vk.com/method/{method}'
    params = {
        'access_token': user_id,
        'v': '5.131',
        'group_id': group_id,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    response = response.json()
    if response.get('error'):
        logging.warning(f"Get server address to upload error: "
                        f"{response['error']['error_msg']}")
    return response['response']['upload_url']


def send_img_to_vk_server(server_url, file_name):
    """Take URL server to upload image and return metadata for saving img"""

    with open(file_name, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(server_url, files=files)
        response.raise_for_status()
    return response.json()


def save_img_to_group_album(uploading_data, user_id, group_id):
    """
    Takes metadata for saving uploaded img from vk server to group album
    Returns photo_id and owner_id for posting photo on wall
    """
    # photos.saveWallPhoto
    method = 'photos.saveWallPhoto'
    url = f'https://api.vk.com/method/{method}'

    #server, photo, hash
    params = {
        'access_token': user_id,
        'group_id': group_id,
        'v': '5.131',
        'server': uploading_data['server'],
        'photo': uploading_data['photo'],
        'hash': uploading_data['hash'],
    }

    response = requests.post(url, params=params)
    response.raise_for_status()
    response = response.json()
    if response.get('error'):
        logging.warning(f"Trying to save uploaded image on server to group "
                        f"album error: "
                        f"{response['error']['error_msg']}")
    photo_and_owner_ids = {
        'owner_id': response['response'][0]['owner_id'],
        'photo_id': response['response'][0]['id'],
    }

    return photo_and_owner_ids


'После успешной загрузки фотографии Вы можете разместить её на стене, опубликовав' \
' запись с помощью метода wall.post и указав идентификатор фотографии в формате ' \
'"photo" + {owner_id} + "_" + {photo_id} (например, "photo12345_654321") в параметре attachments.' \
' В {owner_id} необходимо указывать то же значение, которое пришло Вам в ответе от метода photos.saveWallPhoto.'


def publish_img_on_group_wall(ids, user_id, group_id, message):

    method = 'wall.post'
    url = f'https://api.vk.com/method/{method}'

    # attachments
    attachments = f'photo{ids["owner_id"]}_{ids["photo_id"]}'
    params = {
        'access_token': user_id,
        'v': '5.131',               # API version
        'attachments': attachments, # Name of posted img
        'owner_id': f'-{group_id}', # Group where post
        'from_group': '1',          # Post by group
        'message': message,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    pprint(response.json(), sort_dicts=False)




def main():
    logging.basicConfig(level=logging.DEBUG)

    load_dotenv()
    client_id = os.getenv("VK_APP_CLIENT_ID")
    user_id = os.getenv('VK_USER_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')

    comix_file_name, alt = load_random_xkcd_img()

    server_url = fetch_url_for_upload_img(user_id, group_id)
    uploading_data = send_img_to_vk_server(server_url, comix_file_name)
    owner_photo_ids = save_img_to_group_album(
        uploading_data,
        user_id,
        group_id
    )

    publish_img_on_group_wall(owner_photo_ids, user_id, group_id, alt)

    try:
        os.remove(comix_file_name)
        logging.info(f"File {comix_file_name} was successfully deleted.")
    except FileNotFoundError:
        logging.warning(f"File {comix_file_name} wasn't found for delete.")

if __name__ == "__main__":
    main()