import argparse
import json
import os
import time
from urllib.parse import urljoin
from urllib.parse import urlsplit, unquote

from bs4 import BeautifulSoup
import requests

from download_content import download_image, download_text, get_page, parse_book_page


class ReDirectException(Exception):
    pass


def check_for_redirect_custom(response):
    if response.history:
        raise ReDirectException


def create_json(book, folder=None):
    complete_path = os.path.join(folder, 'book.json')
    with open(complete_path, 'a+', encoding='utf-8') as file:
        json.dump(book, file, ensure_ascii=False, indent=4)
        file.write('\n')


def get_book_id(page_url):
    splited_link = urlsplit(page_url)
    path = unquote(splited_link.path)
    book_id = path[2:-1]
    return book_id


def get_all_links(response):
    soup = BeautifulSoup(response.text, 'lxml')
    all_cards = soup.select('table.d_book')
    all_links = []
    for card in all_cards:
        link = card.select_one('a')['href']
        complete_link = urljoin(response.url, link)
        all_links.append(complete_link)
    return all_links


def get_number_of_pages():
    url = 'https://tululu.org/l55/1'
    response = get_page(url)
    soup = BeautifulSoup(response.text, 'lxml')
    link_selector = 'a.npage'
    links_pages = soup.select(link_selector)
    numbers_lst = [number.text for number in links_pages]
    return numbers_lst[-1]


def main():
    parser = argparse.ArgumentParser(
        description='Скрипт для скачивания книг с https://tululu.org/'
    )
    parser.add_argument('--start_page', default=1, type=int, help='start page')
    parser.add_argument('--end_page', type=int, help='end page')
    parser.add_argument('--dest_folder', default='', type=str, help='dest_folder')
    parser.add_argument('--skip_img', action='store_true', help='skip_image')
    parser.add_argument('--skip_txt', action='store_true', help='skip_text')
    args = parser.parse_args()
    path = args.dest_folder
    if path:
        os.makedirs(path, exist_ok=True)
    start_page = args.start_page
    end_page = args.end_page
    if not end_page:
        end_page = int(get_number_of_pages()) + 1
    counter_errors = 0
    for numb in range(start_page, end_page):
        try:
            template_url = 'https://tululu.org/l55/{}'.format(numb)
            response = requests.get(template_url)
            check_for_redirect_custom(response)
            response.raise_for_status()
            all_links = get_all_links(response)
        except requests.exceptions.HTTPError:
            print('Ошибка HTTP')
        except ReDirectException:
            print('Произошло перенаправление')
        else:
            for link in all_links:
                try:
                    template_url_for_download = 'https://tululu.org/txt.php'
                    response = get_page(link)
                    book = parse_book_page(response)
                    image_url = book['cover']
                    book_id = get_book_id(link)
                    params = {'id': book_id}
                    filename = f"{book_id}-ая книга. {book['name']}"
                    if not args.skip_img:
                        download_image(image_url, book, path)
                    if not args.skip_txt:
                        download_text(template_url_for_download, filename, params, book, path)
                    create_json(book, path)
                except requests.exceptions.HTTPError:
                    print(f'Книга c id {book_id} не существует')
                except requests.exceptions.ConnectionError:
                    counter_errors += 1
                    print(f'Ошибка подключения {counter_errors}')
                    if counter_errors > 1:
                        time.sleep(10)
                        continue


if __name__ == '__main__':
    main()
