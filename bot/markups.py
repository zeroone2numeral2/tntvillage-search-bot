from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup


EXTEND_HELP = InlineKeyboardMarkup([[
    InlineKeyboardButton('più comandi', callback_data='extendhelp')
]])

REDUCE_HELP = InlineKeyboardMarkup([[
    InlineKeyboardButton('riduci', callback_data='reducehelp')
]])
