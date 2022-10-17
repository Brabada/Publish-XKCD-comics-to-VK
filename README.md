# Publish comics XKCD to VK

Project that takes random comics from https://xkcd.com/ by [xkcd API](https://xkcd.com/json.html) and posts them
its with author's comments to group in VK via [VK API](https://vk.com/dev/api_requests).

Group for example: https://vk.com/club216515114


## How to install
For start, you need `Python3` and `pip`.

For installing required packages:
```shell
$ cd "path_where_is_script"
$ pip install -r "requirements.txt"
```

First you need access_token. For obtaining this token you should:
- Register standalone app in VK by this [manual](https://vk.com/dev/first_guide) (article 2);
- Get access_token by [manual above](https://vk.com/dev/first_guide) (article 3) with using [implicit flow](https://vk.com/dev/implicit_flow_user) method;

Then create `.env` file in root of project and add your access_token to `VK_USER_TOKEN`:
```shell
$ cd "path_where_is_script"
$ VK_USER_TOKEN=YOUR_ACCESS_TOKEN > .env
```
Second, put your group/club id to `.env` file as: `VK_GROUP_ID=YOUR_GROUP_ID`.

Example: `VK_GROUP_ID=216515114`. Group id can be obtained from url of your group: vk.com/club**216515114**.

And last, take version VK API from there: https://vk.com/dev/versions. And put this number to `.env` as
`VK_API_VERSION=5.131`.

## How to launch

```shell
$ cd "path_where_is_script"
$ python main.py
```

Output should show link to new post in your group:
```shell
$ python main.py
New post: https://vk.com/wall-216515114_23
```


