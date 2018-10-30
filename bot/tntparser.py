import logging
import os
import requests
import json
import time
from collections import namedtuple
import hashlib

from bs4 import BeautifulSoup

from bot import u

BASE_URL = 'http://www.tntvillage.scambioetico.org/src/releaselist.php'
REQUEST_DATA = {'cat': '0', 'srcrel': ''}
TOTAL_PAGES = 6300

logger = logging.getLogger(__name__)

Torrent = namedtuple('Torrent', [
    'id',
    'title',
    'description',
    'magnet',
    'torrent_download_url',
    'leech',
    'seed'
])
RequestResult = namedtuple('RequestResult', ['soup', 'html'])


class TNTVReleases:
    def __init__(self):
        self._total_pages = 0
        self._torrents = list()
        self._base_file_name = './json_list/tntvillage_releases_{date}.json'
        self._json_base_dir = os.path.normpath('./json_export/')
        self._last_generated_json_filename = ''

    @property
    def json_base_dir(self):
        return self._json_base_dir

    @property
    def torrents(self):
        return [torrent for torrent in self._torrents]

    @staticmethod
    def _fetch_page_by_index(i=1, **kwargs):
        rdata = REQUEST_DATA
        rdata['page'] = str(i)
        result = requests.post(
            BASE_URL,
            data=rdata
        )

        result = RequestResult(
            html=result.text,
            soup=BeautifulSoup(result.text, features='html.parser')
        )
        return result

    @staticmethod
    def _parse_torrent_data(tr):
        title = None
        description = None
        magnet = None
        torrent_download_url = None
        leech = None
        seed = None
        title_md5 = None
        # print(tr)

        leech_node_found = False
        for td in tr.find_all('td'):
            # print('TD:', td)
            if td.find('a'):
                # tutti i <td> che contengono un url
                for a in td.find_all('a', href=True):
                    # print('A:', a)
                    if a['href'].startswith('magnet:?'):
                        magnet = a.get('href', '')
                        logger.debug('magnet: %s', magnet)
                    elif a['href'].startswith('http://forum.tntvillage.scambioetico.org/index.php?showtopic='):
                        title = a.text
                        title_md5 = hashlib.md5(magnet.encode('utf-8')).hexdigest()
                        logger.debug('title: %s', title)
                        logger.debug('title md5: %s', title_md5)
                    elif a['href'].startswith('http://forum.tntvillage.scambioetico.org/index.php') and 'act=Attach' in a['href']:
                        torrent_download_url = a['href']
                        logger.debug('torrent download url: %s', torrent_download_url)
                if td.text:
                    description = td.text
                    logger.debug('description: %s', description)
            elif td.text and td.text.isdigit():
                # leech o seed, prima i leech
                if not leech_node_found:
                    # se non abbiamo ancora trovato il <td> dei leech...
                    leech = int(td.text)
                    seed = int(td.find_next('td').text)  # il "next" sarebbe il <td> con i seed
                    logger.debug('leech: %d, seed: %d', leech, seed)
                    leech_node_found = True  # a questo punto mettiamo questo a True perchè tanto abbiamo sia leech che seed

        if not title or not description or not magnet:
            return None
        else:
            return Torrent(
                id=title_md5,
                title=title,
                description=description,
                torrent_download_url=torrent_download_url,
                leech=leech,
                seed=seed,
                magnet=magnet
            )

    def _fetch_total_pages(self, skip_request_if_present=True):
        if skip_request_if_present and self._total_pages > 0:
            logger.info('skipped request to parse toral number of pages')
            return True

        try:
            logger.info('fetching first page...')
            first_page = self._fetch_page_by_index(i=1)  # l'indice delle pagine inizia da 1
        except Exception as e:
            logger.error('error while requesting the first page: %s', str(e), exc_info=True)
            return False

        logger.info('parsing total pages...')
        for li in first_page.soup.find_all('li', {'class': 'active'}):
            if li.text.lower() == 'ultima':
                tot_pages = int(li.get('p', TOTAL_PAGES))
                logger.info('total pages to fetch: %d', tot_pages)
                self._total_pages = tot_pages
                return True

        return False

    def iter_all(
            self,
            sleep=1,
            reset_previous_list=True,
            limit=0,
            yield_with_current_datetime=True
    ):
        """Fetch all the torrents from all the pages.

        :param sleep: time to wait after every request
        :param reset_previous_list: empty the internal objects list
        :param limit: only fetch this number of pages
        :param yield_with_current_datetime: returns the torrent tuple with the current datetime too
        :return: False if the first request fails, json path if save_json_file is True, else True
        """
        logger.info('fetching all pages (iterable)')

        fetched = self._fetch_total_pages(skip_request_if_present=True)
        if not fetched:
            raise ValueError('cannot fetch total number of pages')

        time.sleep(sleep)
        logger.info('starting loop to fetch all pages (reset_previous_list=%s, limit=%d)', reset_previous_list, limit)
        if reset_previous_list:
            self._torrents = list()

        for i in range(1, self._total_pages + 1 if limit in (None, 0) else limit + 1):
            logger.info('fetching page %d (sleep=%d)...', i, sleep)
            result = self._fetch_page_by_index(i)
            trs = result.soup.find_all('tr')
            logger.info('fetched %d torrents from page %d', len(trs), i)
            torrents_to_yield = list()
            for tr in trs:
                torrent = self._parse_torrent_data(tr)
                if torrent:
                    self._torrents.append(torrent)
                    torrents_to_yield.append(torrent)

            if torrents_to_yield:
                if yield_with_current_datetime:
                    now = u.now(stringify=False)
                    yield [(t.id, t.title, t.description, t.magnet, t.torrent_download_url, t.leech, t.seed, now) for t in torrents_to_yield]
                else:
                    yield [(t.id, t.title, t.description, t.magnet, t.torrent_download_url, t.leech, t.seed) for t in torrents_to_yield]
            else:
                # se il parsing della pagina non ha dato risultati, restituire l'html
                yield result.html

    def save_json_file(self):
        if self._torrents:  # non salvare il file se la lista è rimasta vuota
            file_name = u.now(stringify='tntvillage_releases_%Y%m%d_%H%M.json')
            file_path = os.path.join(self._json_base_dir, file_name)

            json_data = [t._asdict() for t in self._torrents]
            with open(file_path, 'w+') as f:
                json.dump(json_data, f, indent=4)

            return file_path
        else:
            return False

    def get_torrents(self, with_current_datetime=True):
        if not self._torrents:
            return []

        if with_current_datetime:
            now = u.now(stringify=False)
            return [(t.id, t.title, t.description, t.magnet, now) for t in self._torrents]
        else:
            return [(t.id, t.title, t.description, t.magnet) for t in self._torrents]

    def empty_torrents_list(self):
        """Resets the torrents list of the object

        :return: None
        """
        self._torrents = list()
