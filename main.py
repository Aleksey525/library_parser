import os
import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from urllib.parse import urlsplit, unquote


def get_comments(url, filename):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    comments = soup.find_all('div', 'span', class_='texts')
    book_name = filename
    print(book_name)
    if comments:
        for comment in comments:
            print(comment.text.split(')')[-1])
    else:
        print()


def get_file_name(file_link):
    splited_link = urlsplit(file_link)
    file_path = unquote(splited_link.path)
    splited_file_path = os.path.split(file_path)
    file_name = splited_file_path[1]
    return file_name


def get_book_name_with_id(book_id, url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    book_name = title_tag.text.split('::', maxsplit=1)[0].strip()
    return f'{book_id}. {book_name}'


def get_image_url(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    image_link = soup.find('div', class_='bookimage').find('img')['src']
    complete_image_url = urljoin('https://tululu.org/', image_link)
    return complete_image_url


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
    check_for_redirect(response)
    filename = get_file_name(url)
    path = os.path.join(folder, filename)
    with open(path, 'wb') as file:
        file.write(response.content)


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def main():
    book_id = 1
    while book_id <= 10:
        template_url_for_download = 'https://tululu.org/txt.php?id={}'.format(book_id)
        template_url_for_page = 'https://tululu.org/b{}/'.format(book_id)
        try:
            filename = get_book_name_with_id(book_id, template_url_for_page)
            download_text(template_url_for_download, filename)
            image_url = get_image_url(template_url_for_page)
            download_image(image_url)
            get_comments(template_url_for_page, filename)
        except requests.exceptions.HTTPError:
            pass
        book_id += 1


if __name__ == '__main__':
    main()