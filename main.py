import random
import logging
from urllib.parse import urlparse
import os
from pprint import pprint

from dotenv import load_dotenv
import requests


"""=============== XKCD functions section ==============="""
def get_img_name_from_url(url):
    """Extracting image name with extension from url"""

    logging.debug(f"Extracting cfor'ings na: {url}")
    index = url.rfind('/') + 1
    logging.debug(f"Index of beginning name: {index} in {url}")
    return url[index:]


def fetch_xkcd_comics_json(comics_number):
    url = f"https://xkcd.com/{comics_number}/info.0.json"
    response = requests.get(url=url)
    response.raise_for_status()
    return response.json()


def save_xkcd_comics(comics_url):
    """
    Download comics by comics_url and save to the root directory
    Returns comics file name
    """

    response = requests.get(comics_url)
    response.raise_for_status()
    comics = response.content

    comics_file_name = get_img_name_from_url(urlparse(comics_url).path)
    logging.info(f'Comics name: {comics_file_name}')
    with open(comics_file_name, 'wb') as file:
        file.write(comics)
    return comics_file_name


def load_xkcd_comics(comics_number):
    """
    Load xkcd comics from https://xkcd.com/ by comics number and save in
    root directory
    :return: comics file name and description from alt
    """

    try:
        comics_json = fetch_xkcd_comics_json(comics_number)
        alt = comics_json.get('alt')
        comics_url = comics_json.get('img')
        comics_file_name = save_xkcd_comics(comics_url)
    except requests.exceptions.HTTPError:
        logging.warning("Couldn't fetch or save url of xkcd image")
    logging.info(f"Comics {comics_file_name} was loaded and saved in root "
                 f"directory \"{os.path.curdir}\"")
    return comics_file_name, alt


def get_random_xkcd_comics_num():
    response = requests.get('https://xkcd.com/info.0.json')
    response.raise_for_status()
    _to = response.json()['num']
    _from = 1
    return random.randint(_from, _to)


def load_random_xkcd_img():
    """
    Loads random XKCD comics from site and returns comics file name and alt
    """

    try:
        comics_number = get_random_xkcd_comics_num()
    except requests.exceptions.HTTPError:
        logging.warning("Can't load random xkcd comics number due HTTPError")
    return load_xkcd_comics(comics_number)


"""
=============== VK API section ===============
    Publishing of photo to group wall on VK:
    1. Getting server address for loading photo to VK.
    2. Loading photo to the server by address above.
    3. Saving photo to group album from server.
    4. Publish post in group with photo
"""


def fetch_url_for_uploading_img(user_id, group_id):
    """
    Takes group_id and return server address for uploading image
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

    comics_file_name, alt = load_random_xkcd_img()

    server_url = fetch_url_for_uploading_img(user_id, group_id)
    uploading_data = send_img_to_vk_server(server_url, comics_file_name)
    owner_photo_ids = save_img_to_group_album(
        uploading_data,
        user_id,
        group_id
    )

    publish_img_on_group_wall(owner_photo_ids, user_id, group_id, alt)

    try:
        os.remove(comics_file_name)
        logging.info(f"File {comics_file_name} was successfully deleted.")
    except FileNotFoundError:
        logging.warning(f"File {comics_file_name} wasn't found for delete.")

if __name__ == "__main__":
    main()