import os
import requests



def download_books(path, book_id):
    os.makedirs(path, exist_ok=True)
    url_template = 'https://tululu.org/txt.php?id={}/'.format(book_id)
    response = requests.get(url_template)
    check_for_redirect(response)
    response.raise_for_status()
    patch_template = f'{path}/id{book_id}.txt'
    with open(patch_template, 'wb') as file:
        file.write(response.content)


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def main():
    path = 'books'
    books_id = 1
    os.makedirs(path, exist_ok=True)
    while books_id <= 10:
        try:
            download_books(path, books_id)
        except requests.exceptions.HTTPError:
            print('перенаправление')
        books_id += 1


if __name__ == '__main__':
    main()


