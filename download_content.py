import os
import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from urllib.parse import urlsplit, unquote


def get_page(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response


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
