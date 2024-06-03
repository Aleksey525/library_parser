import os
import requests
import urllib.parse


def download_books(path):
    os.makedirs(path, exist_ok=True)
    id = 1
    while id <= 10:
        url_template = 'https://tululu.org/txt.php?id={}/'.format(id)
        response = requests.get(url_template)
        response.raise_for_status()
        patch_template = f'{path}/id{id}.txt'
        with open(patch_template, 'wb') as file:
            file.write(response.content)
        id += 1


def main():
    path = 'books'
    download_books(path)


if __name__ == '__main__':
    main()


