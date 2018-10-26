import logging
import sqlite3
import datetime

import simplesqlitewrap as ssw

from bot import u
import bot.sql as sql


logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = [
    ('last_update', u.now()),
    ('json_file_id', None),
    ('searches_count', 0)
]


class Database(ssw.Database):

    def __init__(self, filename, **kwargs):
        ssw.Database.__init__(self, filename, connection_args={'detect_types': sqlite3.PARSE_DECLTYPES}, **kwargs)

        self._init_tables()

        self._last_update = self._get_general_setting('last_update')  # cache della data/ora dell'ultimo update
        self._json_file_id = self._get_general_setting('json_file_id')
        self._total_entries = 0
        self.update_total_enrties()

    def _init_tables(self):
        self._execute(sql.CREATE_TABLE_TORRENTS)
        self._execute(sql.CREATE_TABLE_GENERAL)
        self._execute(sql.CREATE_TABLE_PARSING_ERRORS)

        self._execute(sql.INSERT_DEFAULT_GENERAL_DATA, DEFAULT_SETTINGS, many=True)  # 'insert or ignore'

    @property
    def total_entries(self):
        return self._total_entries

    @property
    def last_update(self):
        return self._last_update

    @last_update.setter
    def last_update(self, dt):
        self.update_last_update(dt)

    @property
    def json_file_id(self):
        return self._json_file_id

    @json_file_id.setter
    def json_file_id(self, file_id):
        self.update_json_file_id(file_id)

    def insert_torrents(self, torrents_list):
        logger.info('inserting torrents into db, torrents list length: %d', len(torrents_list))
        return self._execute(sql.INSERT_TORRENT, torrents_list, many=True, rowcount=True)

    def _get_general_setting(self, key):
        return self._execute(sql.SELECT_GENERAL_SETTING, (key,), fetchfirst=True)

    def update_total_enrties(self):
        self._total_entries = self._execute(sql.SELECT_TORRENTS_COUNT, fetchfirst=True)

    def search(self, query, **kwargs):
        query = query.strip('%')
        query = '%{}%'.format(query)

        self.increase_searches_count()
        return self._execute(sql.SELECT_TORRENT.format('title'), (query,), fetchall=True, **kwargs)

    def update_last_update(self, dt=None):
        # aggiorna sia variabile di cache che db
        if dt and isinstance(dt, datetime.datetime):
            now = dt.strftime('%d/%m/%Y %H:%M')
        else:
            now = u.now()

        self._last_update = now
        return self._execute(sql.UPDATE_GENERAL_SETTING, (now, 'last_update'), rowcount=True)

    def update_json_file_id(self, file_id):
        # aggiorna sia variabile di cache che db
        self._json_file_id = file_id
        return self._execute(sql.UPDATE_GENERAL_SETTING, (file_id, 'json_file_id'), rowcount=True)

    def insert_error(self, html_string):
        return self._execute(sql.INSERT_PARSING_ERROR, (html_string,), rowcount=True)

    def increase_searches_count(self, increase_by=1):
        return self._execute(sql.UPDATE_QUERIES_COUNT.format(increase_by), rowcount=True)


