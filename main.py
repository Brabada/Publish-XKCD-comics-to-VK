import random
import logging
from urllib.parse import urlparse
import os

from dotenv import load_dotenv
import requests


"""=============== XKCD functions section ==============="""


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
    header, comics_filename = os.path.split(urlparse(comics_url).path)
    logging.info(f'Comics name: {comics_filename}')
    with open(comics_filename, 'wb') as file:
        file.write(comics)
    return comics_filename


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
    else:
        logging.info(f"Comics {comics_file_name} was loaded and saved in root "
                     f"directory \"{os.path.curdir}\"")
        return comics_file_name, alt


def get_random_xkcd_comics_num():
    response = requests.get('https://xkcd.com/info.0.json')
    response.raise_for_status()
    _to = response.json()['num']
    _from = 1
    return random.randint(_from, _to)


def load_random_xkcd_comics():
    """
    Loads random XKCD comics from site and returns comics file name and alt
    """

    try:
        comics_number = get_random_xkcd_comics_num()
    except requests.exceptions.HTTPError:
        logging.error("Can't load random xkcd comics number due HTTPError")
    else:
        return load_xkcd_comics(comics_number)


"""=============== VK API section ==============="""


def fetch_server_url_for_upload_img(access_token, group_id, v):
    """
    Takes access_token, group_id and return vk server url for uploading image
    """

    method = 'photos.getWallUploadServer'
    url = f'https://api.vk.com/method/{method}'
    params = {
        'access_token': access_token,
        'v': v,
        'group_id': group_id,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    response = response.json()
    if response.get('error'):
        logging.error(f"Get server address to upload error: "
                      f"{response['error']['error_msg']}")
        raise requests.exceptions.HTTPError
    return response['response']['upload_url']


def send_img_to_vk_server(server_url, file_name):
    """
    Take server URL for uploading image from file file_name, uploading it
    and return metadata for uploaded image - server, photo, hash
    """

    files = {}
    with open(file_name, 'rb') as file:
        files['photo'] = file
        response = requests.post(server_url, files=files)
    response.raise_for_status()
    response = response.json()
    return response['server'], response['photo'], response['hash']


def save_img_to_group_album(server_url, photo_url, hash, access_token,
                            group_id, v):
    """
    Takes metadata of uploaded img on vk server and saved its to the group
    album.
    Returns photo_id and owner_id of photo in group album
    """

    method = 'photos.saveWallPhoto'
    url = f'https://api.vk.com/method/{method}'

    params = {
        'access_token': access_token,
        'group_id': group_id,
        'v': v,
        'server': server_url,
        'photo': photo_url,
        'hash': hash,
    }

    response = requests.post(url, params=params)
    response.raise_for_status()
    response = response.json()
    if response.get('error'):
        logging.warning(f"Trying to save uploaded image on server to group "
                        f"album error: {response['error']['error_msg']}")
    return response['response'][0]['owner_id'], response['response'][0]['id']


def publish_img_on_group_wall(owner_id, photo_id, access_token, group_id,
                              message, v):
    """
    Publish photo from group album by its photo and owners ids to the group
    wall with message
    Returns post_id of new post in group wall
    """

    method = 'wall.post'
    url = f'https://api.vk.com/method/{method}'

    attachments = f'photo{owner_id}_{photo_id}'
    params = {
        'access_token': access_token,
        'v': v,
        'attachments': attachments,  # Name of posted img
        'owner_id': f'-{group_id}',  # Group where post
        'from_group': '1',           # Post by group
        'message': message,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()['response']['post_id']


def print_link_to_new_post(group_id, post_id):
    link = f"New post: https://vk.com/wall-{group_id}_{post_id}"
    print(link)


def post_comics_on_group_wall(access_token, group_id, v, comics_file_name,
                              message):
    """
    Publishing of photo to group wall on VK:
    1. Getting server address for loading photo to VK.
    2. Loading photo to the server by address above.
    3. Saving photo to group album from server.
    4. Publish post in group with photo.

    access_token - access token from user with rights: photos, groups, wall and
    offline.
    group_id - id of group, can be obtained from
    URL of club. Ex: https://vk.com/club[216515114]
    comics_file_name - comics file name for uploading to server
    message - description of comics that would be in post as text.

    Returns post_id of new post
    """

    vk_server_url = fetch_server_url_for_upload_img(access_token, group_id, v)
    server_url, photo_url, _hash = send_img_to_vk_server(vk_server_url,
                                                comics_file_name)
    owner_id, photo_id = save_img_to_group_album(server_url,
                                                 photo_url,
                                                 _hash,
                                                 access_token,
                                                 group_id, v)
    post_id = publish_img_on_group_wall(owner_id, photo_id, access_token,
                                        group_id, message, v)
    return post_id


def main():
    logging.basicConfig(level=logging.DEBUG)

    load_dotenv()
    access_token = os.getenv('VK_USER_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    vk_api_version = os.getenv('VK_API_VERSION')

    try:
        comics_file_name, alt = load_random_xkcd_comics()

        post_id = post_comics_on_group_wall(access_token,
                                            group_id,
                                            vk_api_version,
                                            comics_file_name,
                                            alt)
        print_link_to_new_post(group_id, post_id)
    except FileNotFoundError:
        logging.exception(f"File {comics_file_name} wasn't found for delete.")
    except requests.exceptions.HTTPError:
        logging.exception(f'There is error while fetching info by API.')
    finally:
        os.remove(comics_file_name)
        logging.info(f"File {comics_file_name} was successfully deleted.")


if __name__ == "__main__":
    main()
