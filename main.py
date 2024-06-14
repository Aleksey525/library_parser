import os
import requests
import argparse
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from urllib.parse import urlsplit, unquote
from download_content import get_page, parse_book_page, download_text, download_image
import time


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
