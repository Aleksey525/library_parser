import os
import requests
import argparse
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from urllib.parse import urlsplit, unquote
import time
import json


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    title_selector = 'h1'
    tag_title = soup.select_one(title_selector)
    book_title = tag_title.text.split('::')[0].strip()
    author = tag_title.text.split('::')[1].strip()
    genres_selector = 'span.d_book a'
    genres = soup.select(genres_selector)
    image_selector = 'div.bookimage img'
    image_link = soup.select_one(image_selector)['src']
    complete_image_url = urljoin(response.url, image_link)
    comments_selectors = 'div.texts span.black'
    comments = soup.select(comments_selectors)

    book = {
        'name': book_title,
        'author': author,
        'genre': [genre.text for genre in genres],
        'cover': complete_image_url,
        'comments': [comment.text for comment in comments]
    }

    return book


def create_json(book, folder=None):
    complete_path = os.path.join(folder, 'book.json')
    with open(complete_path, 'a+', encoding='utf-8') as file:
        json.dump(book, file, ensure_ascii=False, indent=4)
        file.write('\n')


def get_page(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response


def get_book_id(page_url):
    splited_link = urlsplit(page_url)
    path = unquote(splited_link.path)
    book_id = path[2:-1]
    return book_id


def get_all_cards(response):
    soup = BeautifulSoup(response.text, 'lxml')
    all_cards = soup.select('table.d_book')
    all_links = []
    for card in all_cards:
        link = card.select_one('a')['href']
        complete_link = urljoin(response.url, link)
        all_links.append(complete_link)
    return all_links


def get_file_name(file_link):
    splited_link = urlsplit(file_link)
    file_path = unquote(splited_link.path)
    splited_file_path = os.path.split(file_path)
    file_name = splited_file_path[1]
    return file_name


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def download_text(url, filename, params, book, path=None):
    folder = 'books/'
    new_path = os.path.join(path, folder)
    os.makedirs(new_path, exist_ok=True)
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response)
    complete_path = os.path.join(new_path, f'{sanitize_filename(filename)}.txt')
    book['book_path'] = complete_path
    with open(complete_path, 'wb') as file:
        file.write(response.content)


def download_image(url, book, path=None):
    folder = 'images/'
    new_path = os.path.join(path, folder)
    os.makedirs(new_path, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    filename = get_file_name(url)
    complete_path = os.path.join(new_path, filename)
    book['img_src'] = complete_path
    with open(complete_path, 'wb') as file:
        file.write(response.content)


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
    parser.add_argument('--skip_img', default=False, action='store_const', const=True, help='skip_image')
    parser.add_argument('--skip_txt', default=False, action='store_const', const=True, help='skip_text')
    args = parser.parse_args()
    path = args.dest_folder
    if path:
        os.makedirs(path, exist_ok=True)
    start_page = args.start_page
    end_page = args.end_page
    if not end_page:
        end_page = int(get_number_of_pages())
    counter_errors = 0
    for numb in range(start_page, end_page + 1):
        template_url = 'https://tululu.org/l55/{}'.format(numb)
        response = requests.get(template_url)
        all_links = get_all_cards(response)
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
