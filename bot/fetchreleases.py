import logging
import os

from bot.tntparser import TNTVReleases
from bot import config
from bot import db

logger = logging.getLogger(__name__)

tnt = TNTVReleases()


def fetch_releases(bot, job):
    logger.info('running planned job: fetch_releases')

    for torrents_list in tnt.iter_all(reset_previous_list=True, limit=config.tntvillage.limit):
        if isinstance(torrents_list, str):
            # ricevuta una stringa come output, è l'html della pagina di cui il parsing ha restituito 0 risultati
            db.insert_error(html_string=torrents_list)
        elif isinstance(torrents_list, (list, tuple)):
            inserted_rows = db.insert_torrents(torrents_list)
            logger.info('inserted or updated rows: %d', inserted_rows)

            db.update_total_enrties()
            logger.info('total number of torrents in the db: %d', db.total_entries)

            affected_rows = db.update_last_update()  # aggiorna la data dell'ultimo aggiornamento ad adesso
            logger.info('db last update updated. Affected rows: %d; last_update: %s', affected_rows, db.last_update)

    file_path = tnt.save_json_file()
    if config.telegram.chat_id and file_path and file_path is not True:
        try:
            logger.info('sending file %s to chat_id %d', file_path, config.telegram.chat_id)
            with open(file_path, 'rb') as f:
                sent_message = bot.send_document(config.telegram.chat_id, f)

            file_id = sent_message.document.file_id
            logger.info('saving json file_id: %s', file_id)
            affected_rows = db.update_json_file_id(file_id)
            logger.info('saved json file_id. Affected rows: %d; file_id: %s', affected_rows, db.json_file_id)
        except Exception as e:
            logger.error('error while sending/removing the json export: %s', str(e), exc_info=True)
        os.remove(file_path)
