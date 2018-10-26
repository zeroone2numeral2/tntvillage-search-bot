from telegram.ext import Updater

from config import config
import bot.utils as u
import bot.markups as rm
from .database import Database

updater = Updater(token=config.telegram.token)
dispatcher = updater.dispatcher
jobs = updater.job_queue

db = Database(config.database.filename, shared=True)
