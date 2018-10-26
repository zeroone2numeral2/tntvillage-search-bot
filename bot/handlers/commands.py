import logging
from html import escape as html_escape

from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import Filters
from telegram import ChatAction
from telegram import ParseMode

from bot import u
from bot import rm
from bot import db
from config import config

logger = logging.getLogger(__name__)

START_MESSAGE = """Ciao, puoi usarmi per cercare dei torrent dalla lista delle release di TNTVillage.
Ti basta scrivere la parola chiave da cercare

Ispirato dal \
<a href="https://www.reddit.com/r/italy/comments/9pv9l3/tntvillage_magnet_links_in_caso_andasse_di_nuovo/">\
post di u/different789_</a>\
"""

HELP_MESSAGE = """<b>Comandi</b>
- qualasiasi messaggio: cerca nella lista dei torrent
- /json: ricevi un file json contenente l'ultima lista delle release salvata

<b>Info varie</b>
- la lista viene aggiornata ogni {updated_every} ore, TNTVillage permettendo
- <code>%</code> può essere usato come carattere jolly nelle proprie query di ricerca. Significa "zero o più \
caratteri qualsiasi" (ad esempio, "<i>notte%leoni</i>" restituirà tutti i torrent che contengono le parole \
"<i>notte</i>" e "<i>leoni</i>" nel titolo). Di default, questo carattere viene aggiunto all'inizio ed alla fine \
di tutte le query
- c'è un limite al numero di torrent restituiti da una ricerca. Per filtrare ulteriormente i risultati, sii più \
specifico nel cercare il nome del torrent\
""".format(updated_every=round(config.tntvillage.update_frequency / 3600, 2))

MAGNET_MESSAGE = """<b>{title}</b>
<pre>{magnet}</pre>

<b>Perchè non lo vedo come un link?</b> Purtroppo Telegram non permette di creare \
<a href="https://t.me/{bot_username}">hyperlink</a> con URI magnet, quindi quella del deeplink era la soluzione più \
semplice da implementare. Da Android/iOs, tieni premuto il dito sul magnet per copiarlo\
"""


@u.action(ChatAction.TYPING)
@u.failwithmessage
def on_help_command(bot, update):
    logger.debug('/help command')

    update.message.reply_html(HELP_MESSAGE, disable_web_page_preview=True)


@u.action(ChatAction.TYPING)
@u.failwithmessage
def on_start_command(bot, update):
    logger.debug('/start')

    text = START_MESSAGE
    source_code_url = config.other.get('source_code', None)
    if source_code_url:
        text = '{0}\n\n<a href="{1}">codice sorgente</a>'.format(text, source_code_url)

    update.message.reply_html(text, disable_web_page_preview=True, reply_markup=rm.EXTEND_HELP)


@u.action(ChatAction.UPLOAD_DOCUMENT)
@u.failwithmessage
def on_json_command(bot, update):
    logger.debug('/json')

    update.message.reply_text('Purtroppo Telegram non permette di inviare file > 50mb, '
                              'ed il json dei torrent è troppo grande :(\n'
                              'Al momento questo comando è disabilitato')
    return

    if not db.json_file_id:
        update.message.reply_text('Mi dispiace, nessun file al momento disponibile')
    else:
        update.message.reply_document(db.json_file_id)


@u.action(ChatAction.TYPING)
@u.failwithmessage
def on_deeplink(bot, update, args, user_data):
    logger.debug('/start deeplink')

    torrent_id = args[0]
    torrent = user_data['query_result'].get(torrent_id, None)
    if not torrent:
        logger.error('deeplink: cannot find torrent with id %s in the user_data dictionary', torrent_id)
        update.message.reply_text('Whoops, qualcosa è andato storto, non riesco più a ricavare il magnet di questo '
                                  'torrent')
        return

    # non rimuovere il dict coi risultati della ricerca,
    # l'utente potrebbe usare i deeplink nei risultati più volte
    # user_data.pop('query_result')
    text = MAGNET_MESSAGE.format(title=html_escape(torrent.title), magnet=html_escape(torrent.magnet),
                                 bot_username=bot.username)
    update.message.reply_html(text, disable_web_page_preview=True)


def on_extend_cq(bot, update):
    logger.debug('extend callback query')

    update.callback_query.message.edit_text(HELP_MESSAGE, reply_markup=rm.REDUCE_HELP, parse_mode=ParseMode.HTML)


def on_reduce_cq(bot, update):
    logger.debug('reduce callback query')

    text = START_MESSAGE
    source_code_url = config.other.get('source_code', None)
    if source_code_url:
        text = '{0}\n\n<a href="{1}">codice sorgente</a>'.format(text, source_code_url)

    update.callback_query.message.edit_text(text, reply_markup=rm.EXTEND_HELP, disable_web_page_preview=True,
                                            parse_mode=ParseMode.HTML)


HANDLERS = (
    CommandHandler('help', on_help_command),
    CommandHandler('start', on_deeplink, filters=Filters.regex(r'^\/start\s'), pass_user_data=True, pass_args=True),
    CommandHandler('start', on_start_command),
    CommandHandler('json', on_json_command),
    CallbackQueryHandler(on_extend_cq, pattern=r'^extendhelp$'),
    CallbackQueryHandler(on_reduce_cq, pattern=r'^reducehelp$')
)
