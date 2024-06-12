import os
import requests
import argparse
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from urllib.parse import urlsplit, unquote
import time


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    tag_title = soup.find('h1')
    book_title = tag_title.text.split('::', maxsplit=1)[0].strip()
    author = tag_title.text.split('::', maxsplit=1)[1].strip()
    genres = soup.find('span', class_='d_book').find_all('a')
    image_link = soup.find('div', class_='bookimage').find('img')['src']
    complete_image_url = urljoin(response.url, image_link)
    comments = soup.find_all('div', 'span', class_='texts')

    book = {
        'name': book_title,
        'author': author,
        'genre': [genre.text for genre in genres],
        'cover': complete_image_url,
        'comments': [comment.text.split(')')[-1] for comment in comments]
    }

    return book


def get_page(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response


def get_file_name(file_link):
    splited_link = urlsplit(file_link)
    file_path = unquote(splited_link.path)
    splited_file_path = os.path.split(file_path)
    file_name = splited_file_path[1]
    return file_name


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def download_text(url, filename, params, folder='books/'):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response)
    path = os.path.join(folder, f'{sanitize_filename(filename)}.txt')
    with open(path, 'wb') as file:
        file.write(response.content)


def download_image(url, folder='images/'):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    filename = get_file_name(url)
    path = os.path.join(folder, filename)
    with open(path, 'wb') as file:
        file.write(response.content)


def main():
    parser = argparse.ArgumentParser(
        description='Скрипт для скачивания книг с https://tululu.org/'
    )
    parser.add_argument('--start_id', default=1, type=int, help='start book id')
    parser.add_argument('--end_id', default=10, type=int, help='end book id')
    args = parser.parse_args()
    book_id = args.start_id
    counter_errors = 0
    while book_id <= args.end_id:
        params = {'id': book_id}
        template_url_for_download = 'https://tululu.org/txt.php'
        template_url_for_page = 'https://tululu.org/b{}/'.format(book_id)
        try:
            response = get_page(template_url_for_page)
            book = parse_book_page(response)
            filename = f"{book_id}. {book['name']}"
            download_text(template_url_for_download, filename, params)
            image_url = book['cover']
            download_image(image_url)
        except requests.exceptions.HTTPError:
            print(f'Книга с id{book_id} не существует')
        except requests.exceptions.ConnectionError:
            counter_errors += 1
            print(f'Ошибка подключения {counter_errors}')
            if counter_errors > 1:
                time.sleep(10)
                continue
        book_id += 1


if __name__ == '__main__':
    main()