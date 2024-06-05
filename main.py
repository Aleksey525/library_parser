import os
import requests
import argparse
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from urllib.parse import urlsplit, unquote


def parse_book_page(page_url):
    response = requests.get(page_url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    tag_title = soup.find('h1')
    book_title = tag_title.text.split('::', maxsplit=1)[0].strip()
    author = tag_title.text.split('::', maxsplit=1)[1].strip()
    genres = soup.find('span', class_='d_book').find_all('a')
    image_link = soup.find('div', class_='bookimage').find('img')['src']
    complete_image_url = urljoin('https://tululu.org/', image_link)
    comments = soup.find_all('div', 'span', class_='texts')

    parse_result = {'name': book_title,
             'author': author,
             'genre': [genre.text for genre in genres],
             'cover': complete_image_url,
             'comments': [comment.text.split(')')[-1] for comment in comments]
             }

    return parse_result


def get_file_name(file_link):
    splited_link = urlsplit(file_link)
    file_path = unquote(splited_link.path)
    splited_file_path = os.path.split(file_path)
    file_name = splited_file_path[1]
    return file_name


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def download_text(url, filename, folder='books/'):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(url)
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
    while book_id <= args.end_id:
        template_url_for_download = \
            'https://tululu.org/txt.php?id={}'.format(book_id)
        template_url_for_page = 'https://tululu.org/b{}/'.format(book_id)
        try:
            parse_result = parse_book_page(template_url_for_page)
            filename = f"{book_id}. {parse_result['name']}"
            download_text(template_url_for_download, filename)
            image_url = parse_result['cover']
            download_image(image_url)
        except requests.exceptions.HTTPError:
            print(f'Книга с id{book_id} не существует')
        book_id += 1


if __name__ == '__main__':
    main()
