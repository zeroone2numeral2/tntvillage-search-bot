import logging
import datetime
from functools import wraps
from html import escape as html_escape

logger = logging.getLogger(__name__)


def action(chat_action):
    def real_decorator(func):
        @wraps(func)
        def wrapped(bot, update, *args, **kwargs):
            bot.send_chat_action(update.effective_chat.id, chat_action)
            return func(bot, update, *args, **kwargs)

        return wrapped

    return real_decorator


def failwithmessage(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        try:
            return func(bot, update, *args, **kwargs)
        except Exception as e:
            logger.error('error while running handler callback: %s', str(e), exc_info=True)
            text = 'An error occurred while processing the message: <code>{}</code>'.format(html_escape(str(e)))
            if update.callback_query:
                update.callback_query.message.reply_html(text)
            else:
                update.message.reply_html(text)

    return wrapped


def now(stringify='%d/%m/%Y %H:%M'):
    dtnow = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    if not stringify:
        return dtnow
    else:
        return dtnow.strftime(stringify)
