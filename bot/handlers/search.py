import logging
from html import escape as html_escape

from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram import ChatAction

from bot import u
from bot import db

logger = logging.getLogger(__name__)


MAX_RESULT_ITEMS = 40

TORRENT_ROW = """- {title} [{leech}/{seed}]\
[<a href="https://t.me/{bot_username}?start={id}">magnet</a>][<a href="{torrent_url}">torrent</a>]"""

BOTTOM_TEXT = """<i>{0} risultati di {1}</i>
I numeri tra parentesi accanto al titolo del torrent corrispondono a leech/seed
<b>Torrent nel database</b>: {2:,}
<b>Ultimo aggiornamento lista</b>: {3}"""


def truncate(string, max_length=80):
    if len(string) > max_length:
        return string[:max_length] + '...'
    else:
        return string


@u.action(ChatAction.TYPING)
@u.failwithmessage
def on_search_query(bot, update, user_data):
    logger.debug('search query')

    query = update.message.text

    if len(query.replace('%', '')) < 3:
        update.message.reply_text('Il testo da cercare deve contenere almeno 3 caratteri (escluso il carattere jolly)')
        return

    torrents_list = db.search(query, as_namedtuple=True)
    if not torrents_list:
        update.message.reply_text('Non ho trovato alcun torrent che soddisfa la tua ricerca')
        return

    # massimo 100 entities in un msg
    strings_list = list()
    for t in torrents_list[:MAX_RESULT_ITEMS]:
        string = TORRENT_ROW.format(
            title=html_escape(truncate(t.title)),
            bot_username=bot.username,
            id=t.id,
            torrent_url=t.torrent_download_url,
            leech='-' if t.leech is None else t.leech,
            seed='-' if t.seed is None else t.seed
        )
        strings_list.append(string)

    # salva un dizionario di {id: magnet} per restituire il magnet quando l'utente aprirà il deeplink (senza eseguire
    # una nuova query al db)
    user_data['query_result'] = {t.id: t for t in torrents_list}

    text = '{0}\n\n{1}'.format(
        '\n'.join(strings_list),
        BOTTOM_TEXT.format(
            MAX_RESULT_ITEMS,
            len(torrents_list),
            db.total_entries,
            db.last_update
        )
    )
    update.message.reply_html(text, disable_web_page_preview=True)


HANDLERS = (
    MessageHandler(Filters.text, on_search_query, pass_user_data=True),
)
