import os
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
LOGS_CHAT_ID = os.environ.get('LOGS_CHAT_ID')
DATABASE_URL = os.environ.get('DATABASE_URL')
ADMINS = os.environ.get('ADMINS').split(',')
RESTART_COMMAND = os.environ.get('RESTART_COMMAND')

bot = Bot(token=BOT_TOKEN)