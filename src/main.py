import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL,
                       PEP_URL, RESULTS, RESULTS_VERSIONS, RESULTS_PEP)
from outputs import control_output
from exceptions import NotFoundVersionsPythonList
from utils import find_tag, get_response


logger = logging.getLogger(__name__)


def whats_new(session):
    """
    Функция для парсинга нововведений в Python.
    """
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(
        main_div,
        'div',
        attrs={'class': 'toctree-wrapper compound'}
    )
    section_by_python = div_with_ul.find_all(
        'li',
        attrs={'class': 'toctree-l1'}
    )
    for section in tqdm(section_by_python, desc='Super parser'):
        get_tag = section.find('a')
        href = get_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        RESULTS.append(
            (version_link, h1.text, dl_text,),
        )
    return RESULTS


def latest_versions(session):
    """
    Функция для парсинга текущих версиях Python.
    """
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise NotFoundVersionsPythonList('Не найден список c версиями Python.')
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a in a_tags:
        link = a['href']
        text_match = re.search(pattern, a.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a.text, ''
        RESULTS_VERSIONS.append(
            (link, version, status,),
        )
    return RESULTS_VERSIONS


def download(session):
    """
    Функция-парсер для скачивания документации по Python.
    """
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    get_table = find_tag(soup, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(
        get_table,
        'a',
        {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response_archive = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response_archive.content)
    logger.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    """
    Функция для парсинга статусов PEP.
    """
    response = get_response(session, PEP_URL)
    soup = BeautifulSoup(response.text, 'lxml')
    tables_of_all_documents_pep = soup.find(
        'section',
        attrs={'id': 'numerical-index'}
    )
    get_tbody = tables_of_all_documents_pep.find('tbody')
    all_ = get_tbody.find_all('tr')
    pep_count = 0
    status_count = defaultdict(int)
    for item in tqdm(all_, desc='pep parsing'):
        get_a = item.find('a')
        get_status = item.find('abbr')
        if get_a is None:
            continue
        link = get_a['href']
        link_url = urljoin(PEP_URL, link)
        status_pep = get_status.text[1:]
        response = get_response(session, link_url)
        soup = BeautifulSoup(response.text, 'lxml')
        get_dl_tag = find_tag(
            soup,
            'dl',
            attrs={'class': 'rfc2822 field-list simple'}
        )
        pattern = (
            r'.*(?P<status>Active|Draft|Final|Provisional|Rejected|'
            r'Superseded|Withdrawn|Deferred|April Fool!|Accepted)'
        )
        search_text = re.search(pattern, get_dl_tag.text)
        status = None
        if search_text:
            status = search_text.groups('status')
        if status_pep and EXPECTED_STATUS.get(status_pep) != status:
            logger.info(
                f'Несовпадающие статусы:\n{link_url}\n'
                f'Статус в карточке: {status}\n'
                f'Ожидаемый статус: {EXPECTED_STATUS[status_pep]}'
            )
        if not status_pep and status not in ('Active', 'Draft'):
            logger.info(
                f'Несовпадающие статусы:\n{link}\n'
                f'Статус в карточке: {status}\n'
                f'Ожидаемые статусы: ["Active", "Draft"]'
            )
        pep_count += 1
        status_count[status] += 1
    RESULTS_PEP.append([(status, status_count[status],)
                        for status in status_count])
    RESULTS_PEP.append(('Total', pep_count,))
    return RESULTS_PEP


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logger.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logger.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parse_mode = args.mode
    results = MODE_TO_FUNCTION[parse_mode](session)
    if results is not None:
        control_output(results, args)
    logger.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
