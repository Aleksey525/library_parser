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


def create_json(book):
    with open('book.json', 'a+', encoding='utf-8') as file:
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
    counter_errors = 0
    for numb in range(1, 2):
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
                download_image(image_url)
                download_text(template_url_for_download, filename, params)
                create_json(book)
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
